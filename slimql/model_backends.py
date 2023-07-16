import importlib.util

class LLMBackend:
    def __init__(self, constructor, init_kwarg_string):
        self.constructor = None
        self.init_kwarg_string = init_kwarg_string
        self.import_string = ""

    # @property
    # def import_string(self):
    #     return self.import_string

    @property
    def init_string(self):
        if self.constructor:
            return f'{self.constructor}({self.init_kwarg_string})'
        return ""

    def call_string(self, stop_phrases=[]):
        raise NotImplementedError


class LlamaCPP(LLMBackend):
    def __init__(self, init_kwarg_string):
        """
        model_path: path to compiled llama.cpp model
        kwargs: kwargs to pass to llama_cpp.Llama constructor
        """
        assert importlib.util.find_spec("llama_cpp") is not None, "llama-cpp-python is not installed"
        self.import_string = "from llama_cpp import Llama"
        self.constructor = "Llama"
        self.init_kwarg_string = init_kwarg_string

    def call_string(self, stop_phrases=[]):
        stop_phrases_string = "stop=[" + ", ".join([repr(s) for s in stop_phrases]) + "]"
        return f"llm(prompt=''.join(prompt), {stop_phrases_string})['choices'][0]['text']"


class BackendRegistry:
    def __init__(self):
        self.backends = {}

    def register(self, name, backend):
        self.backends[name] = backend

    def __contains__(self, name):
        return name in self.backends

    def __getitem__(self, name):
        if not name in self.backends:
            raise KeyError(f"Backend {name} not registered")
        return self.backends[name]

llm_backend_registry = BackendRegistry()
llm_backend_registry.register("LlamaCPP", LlamaCPP)




