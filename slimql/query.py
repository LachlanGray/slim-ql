import re
import inspect
import os
import importlib.util

from .model_backends import llm_backend_registry

class SegmentedQuery:
    def __init__(self, query: str):
        segment = "preamble"

        query = query.split("\n")
        query = [line.replace("\\n", r"\n") for line in query]

        self.preamble = []
        self.sample = []
        self.from_ = []
        self.where = []

        for line in query:
            if line.startswith("sample"):
                segment = "sample"
                continue
            if line.startswith("from"):
                segment = "from_"
                continue
            if line.startswith("where"):
                assert segment == "from_", "where must come after from"
                segment = "where"
                continue

            getattr(self, segment).append(line)


class CompiledQuery:
    def __init__(self, query: str, *args, parent_frame_var_names=None, **kwargs):
        self.segments = SegmentedQuery(query)
        self.variables = {} # doesn't hold state just metadata
        self.args = args
        self.kwargs = kwargs

        self.llm_backend = None

        self.parent_frame_var_names = parent_frame_var_names

        # self.model_definitions = []
        self.sample = []
        self.from_ = []
        self.where = []

        self.compiled = []

        self.compiled += self.segments.preamble
        self.parse_model()
        self.parse_constraints()
        self.parse_prompt()


    def parse_model(self):
        model = self.segments.from_[0].strip().split("(")[0]
        init_args = self.segments.from_[0].strip().split("(")[1][:-1]
        self.llm_backend = llm_backend_registry[model](init_args)
        self.compiled = [self.llm_backend.import_string] + self.compiled

        # path = self.segments.from_[0].strip().split("(")[0]
        # self.model_init_string = f"llm = Llama(model_path={path}, n_gpu_layers=1, verbose=False)"

    def parse_constraints(self):
        for line in self.segments.where:
            line = line.strip()
            if line.startswith("stops "):
                line = line[6:]
                variable = line.split(" ")[0]
                line = line[len(variable)+1:]
                stop_phrases = line.split(", ")
                stop_phrases = [s.replace('\\n', '\n') for s in stop_phrases]
                self.variables[variable] = {}
                self.variables[variable]["stop_phrases"] = stop_phrases
            elif line.startswith("matches "):
                raise NotImplementedError("matches doesn't do anything")
                line = line[6:]
                variable = line.split(" ")[0]
                line = line[len(variable)+1:]
                self.variables[variable]["pattern"] = line
            else:
                if line.strip():
                    raise NotImplementedError(f"No constraint for {line}")

    def extract_variables(self, line):
        variables = re.findall(r'\[(.*?)\]', line)
        variables = [v.strip() for v in variables]
        for name in variables:
            # name = v.split(" ")[0]
            if name in self.variables:
                continue
            self.variables[name] = {}

    def parse_prompt(self):
        arg_string = ", ".join([arg for arg in self.args])
        if not arg_string:
            arg_string = "*args"
        else:
            arg_string += ", *args"

        kwarg_string = ", ".join([f'{kw}={repr(default)}' for kw, default in self.kwargs.items()])
        if not kwarg_string:
            kwarg_string = "**kwargs"
        else:
            kwarg_string += ", **kwargs"

        self.compiled.append(f"def query({arg_string}, parent_frame_vars=None, {kwarg_string}):")

        # self.compiled.append(f"    {self.model_init_string}")
        self.compiled.append(f'    llm = {self.llm_backend.init_string}')

        if self.parent_frame_var_names:
            for name in self.parent_frame_var_names:
                self.compiled.append(f"    {name} = parent_frame_vars['{name}']")

        self.compiled.append("    prompt = []")

        for line in self.segments.sample:
            if line.strip().startswith("\""):
                indent = len(line) - len(line.lstrip())
                line = line.strip()
                line = line[1:]
                if line.endswith("\""):
                    line = line[:-1]

                line = line.replace(r'\[', '<lbracket>').replace(r'\]', '<rbracket>')
                self.extract_variables(line)
                parts = re.split(r'(\[.*?\])', line)
                parts = [part for part in parts if part]
                parts = [part.replace('<lbracket>', '[').replace('<rbracket>', ']') for part in parts]

                for prompt_or_hole in parts:
                    if prompt_or_hole.startswith('['): # is prompt
                        prompt_or_hole = prompt_or_hole[1:-1]
                        stop_phrases = self.variables[prompt_or_hole].get('stop_phrases', [])
                        call_str = self.llm_backend.call_string(stop_phrases=stop_phrases)
                        self.compiled.append(f"{indent*' '}{prompt_or_hole} = {call_str}")

                        # if 'stop_phrases' in self.variables[prompt_or_hole]:
                        #     self.compiled.append(f"{indent*' '}{prompt_or_hole} = llm(''.join(prompt), stop=[{', '.join([repr(s) for s in self.variables[prompt_or_hole]['stop_phrases']])}])['choices'][0]['text']")
                        # else:
                        #     self.compiled.append(f"{indent*' '}{prompt_or_hole} = llm(''.join(prompt))['choices'][0]['text']")

                        self.compiled.append(f"{indent*' '}prompt.append({prompt_or_hole})")
                    else: # is prompt
                        line = indent*' ' + f"prompt.append(f\"{prompt_or_hole}\")"
                        self.compiled.append(line)

            else:
                self.compiled.append(line)

    def __str__(self):
        return "\n".join(self.compiled)

def query(fct):
    source = inspect.getsource(fct)
    lines = source.split("\n")
    lines = lines[1:]
    global_indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[global_indent:] for line in lines]
    function_name, args, kwargs = parse_function_def(lines[0])
    filename = f'./compiled/{function_name}.py'

    # Get local and global variables from the calling frame
    calling_frame = inspect.stack()[1]
    local_vars = {k: v for k, v in calling_frame.frame.f_locals.items() if not k.startswith('_')}
    local_vars.pop("query", None)
    global_vars = {k: v for k, v in calling_frame.frame.f_globals.items() if not k.startswith('_')}
    global_vars.pop("query", None)

    parent_frame_vars = {**global_vars, **local_vars}
    parent_frame_vars = {k: v for k, v in parent_frame_vars.items() if not k in args and not k in kwargs}

    # # Merge them into the kwargs, giving preference to the original kwargs
    # kwargs = {**global_vars, **local_vars, **kwargs}
    # input(f"{kwargs}")

    dedented_lines = []
    for line in lines[2:]:
        if line.strip() in ["\"\"\"", "'''"]:
            break
        dedented_lines.append(line[4:])

    source = "\n".join(dedented_lines)
    compiled = CompiledQuery(source, *args, parent_frame_var_names=parent_frame_vars.keys(), **kwargs)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(str(compiled))

    # import compiled file as module
    spec = importlib.util.spec_from_file_location("new_module", filename)
    new_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new_module)

    new_fct = getattr(new_module, "query")

    def wrapper(*args, **kwargs):
        return new_fct(*args, parent_frame_vars=parent_frame_vars, **kwargs)

    return wrapper

def parse_function_def(function_def):
    pattern = r"def\s+(?P<name>\w+)\s*\((?P<args>.*?)\)\s*:"
    match = re.search(pattern, function_def)
    func_name = match.group("name")
    args = [arg.strip() for arg in match.group("args").split(",")]
    pos_args = [arg for arg in args if "=" not in arg]
    kw_args = [arg for arg in args if "=" in arg]
    kw_args = {arg.split("=")[0]: eval(arg.split("=")[1]) for arg in kw_args}

    return func_name, pos_args, kw_args
