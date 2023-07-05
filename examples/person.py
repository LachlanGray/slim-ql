from slimql import query

class Person:
    def __init__(self, name):
        self.name = name
        self.introduction = ""

    @query
    def introduce(self):
        '''
        sample
            if self.introduction:
                return self.introduction
            "Hi, I'm {self.name}. I'm known for [intro]"
            self.last_intro = "I'm known for " + intro
            return "".join(prompt)
        from
            LlamaCPP(model_path="models/path/to/compiled-ggml-model.bin", n_gpu_layers=1, verbose=False)
        where
            stops intro \n
        '''
        pass

assistant = Person("a language model")
intro = assistant.introduce()
print(intro)

# Hi, I'm a language model. I'm known for generating text.

