import bat_ai
import argparse

def process_input(question,file):
    inputs = {"question": question,"path" : file} 
    for output in bat_ai.app.stream(inputs):
        for key, value in output.items():
            print(f"{key}:")
    
    generation = value["generation"]
    text_without_newlines = generation.replace('\n', '')
    print(f"Output: {text_without_newlines}")
    return text_without_newlines


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze log file for errors")
    parser.add_argument("log_path", help="Path to the log file")
    parser.add_argument("--question", default="Analyze the log file and find the failure messages from the same", help="Question to ask about the log file")
    args = parser.parse_args()
    resposne = process_input(args.question,args.log_path)
