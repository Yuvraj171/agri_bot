import whisper
import gradio as gr

def transcribe_audio(audio_file):
    model=whisper.load_model("base")
    result = model.transcribe(audio_file, fp16=False)
    return result["text"]




def main():
    audio_input = gr.Audio(sources="upload",type="filepath")
    output = gr.Textbox()
    
    iface = gr.Interface(
    fn=transcribe_audio,
    inputs=audio_input,
    outputs=output
    )
    iface.launch()
    
    
if __name__ == "__main__":
    main()