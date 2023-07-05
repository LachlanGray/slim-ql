# sLiMQL
A small, synchronous prompting language focused on local inference with [LMQL](https://github.com/eth-sri/lmql/tree/main)-like syntax.

Currently only works with [llama.cpp](https://github.com/ggerganov/llama.cpp) compiled models, but it's possible to plug anything in (documentation pending; see `model_backends.py::LlamaCPP`).

## Installation
Right now [llama-cpp-python](https://llama-cpp-python.readthedocs.io/en/latest/) is the only dependency. It's on PyPI but if you are on apple silicon, install it before `slmql` following [these instructions](https://llama-cpp-python.readthedocs.io/en/latest/install/macos/).

Once `llama-cpp-python` is working you can install `slimql` with:
```
pip install git+https://github.com/LachlanGray/slim-ql.git
```

## Usage
All prompting is done through decorated functions that work like `@lmql.query` functions.

In a nutshell:
- There is a `sample`, `from`, and `where` segment in each prompt
    - `sample` contains the main prompt template
    - `from` specifies the model(s) being used
    - `where` (optional) specifies conditions/constraints for generated variables
- Each line in `sample` is either enclosed in double quotes `""` or not. 
    - If it is, this is a *prompt line* and the line is appended to the prompt
    - If not, the line is executed as python
- Prompt lines treat curly braces `{}` the same way as f-strings. I.e. if you have a function-local variable `x`, then you can insert it into the prompt as
    ```
    ...
    "This prompt line says that x is {x}"
    ...
    ```
- Prompt lines treat square brackets `[]` as *holes* to fill. The model will generate text to fill the hole, the new text will be added to the prompt, *and* the new text will be assigned to a local variable named after the hole.
    ```
    ...
    "The answer to the question of the meaining of life is [answer]"
    assert answer == '42'
    ...
    ```
- You can enjoy loops, if structures, and your other favourite python activities in the prompt
- `return` statements can go anywhere in the prompt
- For now, the `from` clause takes one single path that leads to a compiled llama.cpp model
- For now, the `where` clause only lets you specify the stopping conditions for each hole. The syntax is `stops hole_variable <comma-space separated stop tokens>`.


## Example
You can query language models with a python function like this:
```
from slimql import query

@query
def would_say_to(person1, person2, n=5):
    """
    sample
        phrases = []
        "These are {n} things {person1} would say to {person2}:\n"
        for i in range(n):
            "{i+1}) [phrase]\n"
            phrases.append(phrase)
        return phrases
    from
        LlamaCPP(model_path="models/3B/orca_mini_3B-GGML/orca-mini-3b.ggmlv3.q4_0.bin", n_gpu_layers=1, verbose=False)
    where
        stops phrase \n, .
    """

x = would_say_to("Socrates the philosopher", "Garfield the cat")
print(x)
```

outputs:
```
['Καλωσοφία (Kalósophía) - "Wisdom"', 'ΧΕΙΡΟΣ (Chērios) - "Beautiful"', 'ΛΑΚΩΝ (Lakón) - "Generous"', 'ΤΥΠΟΣ (Tupós) - "F
riendship"', 'ΨΥΧΗ (Psyché) - "Soul"']
```

Under the hood, the final state of the prompt is
```
These are 5 things Socrates the philosopher would say to Garfield the cat:
1) Καλωσοφία (Kalósophía) - "Wisdom"
2) ΧΕΙΡΟΣ (Chērios) - "Beautiful"
3) ΛΑΚΩΝ (Lakón) - "Generous"
4) ΤΥΠΟΣ (Tupós) - "Friendship"
5) ΨΥΧΗ (Psyché) - "Soul"
```

The prompt is a growing list which can be accessed as `prompt`, e.g. you could end the `sample` segment with `return "".join(prompt)` and this is what the function would return.


## TODO
Most of this was done in one night so there's plenty to add, and it probably has *surprise features*.

Some things:
- documentation (will do it when I'm back)
- Dynamic control of generation parameters
- Regex constraints
