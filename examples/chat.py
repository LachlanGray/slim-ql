from slmql import query

@query
def chat():
    '''
    user = "\n\n### User:\n"
    assistant = "\n\n### Response:\n"
    system = "\n\n### System:\n"
    sample
        print("\033c")
        "{system}You are an AI assistant that follows instruction extremely well. Help as much as you can"
        user_message = input('> ')
        "{user}{user_message}"
        while user_message != "exit":
            "{assistant}[assistant_message]"
            print("\n" + assistant_message + "\n")
            user_message = input('> ')
            "{user}{user_message}"
        return "".join(prompt)
    from
        LlamaCPP(model_path="models/path/to/compiled-ggml-model.bin", n_gpu_layers=1, verbose=False)
    '''

convo = chat()

# > Hello, who is this?
#
#  I'm sorry, but I don't have any information about a person or entity named "this". Can you please provide me with more c
# ontext so I can help you better?
#
# > I see how it is
#
#  I'm sorry, I cannot help you if you are not clear on your request. Could you please provide me with more information or 
# context so that I can assist you better?
#
# > exit


