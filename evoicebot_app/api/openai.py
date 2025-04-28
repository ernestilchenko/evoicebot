import base64

from django.conf import settings
from openai import OpenAI


def analyze_document(file, file_type):
    try:
        file_data = file.read()
        file.seek(0)

        if len(file_data) > 10 * 1024 * 1024 or file_type not in ['pdf', 'txt', 'doc', 'docx']:
            return None

        base64_string = base64.b64encode(file_data).decode("utf-8")
        mime_type = "application/pdf"
        if file_type == 'txt':
            mime_type = "text/plain"
        elif file_type in ['doc', 'docx']:
            mime_type = "application/msword"

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": file.name,
                            "file_data": f"data:{mime_type};base64,{base64_string}",
                        },
                        {
                            "type": "input_text",
                            "text": "Przeanalizuj treść tego dokumentu i napisz krótkie streszczenie jego zawartości w języku polskim (maksymalnie 100 słów).",
                        },
                    ],
                },
            ]
        )

        return response.output_text

    except Exception as e:
        print(f"Error processing document with AI: {e}")
        return None


def generate_speech(text, voice="alloy", format="wav"):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": voice, "format": format},
        messages=[
            {
                "role": "user",
                "content": text
            }
        ]
    )

    wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
    text_response = completion.choices[0].message.content

    return {
        "audio_data": wav_bytes,
        "text_response": text_response
    }


def save_audio_file(audio_data, filename="output.wav"):
    with open(filename, "wb") as f:
        f.write(audio_data)
