import openai 
from google.cloud import speech
import io
import subprocess
import os

import config   # 본인의 key 모은 모듈

###############    must change it to your KEY   #######################
# 발급받은 API 키 설정, 명령 어떻게 수행할지 작성
OPENAI_API_KEY = config.OPENAI_API_KEY
# 사용할 파일 위치
LOCAL_FILE_PATH = './out.raw'  #파일 명을 꼭 확인하자.
#######################################################################

###############   freely change to your AGV    ########################
LANGUAGE = "en-US"
MODEL = "gpt-3.5-turbo"
GPT_MESSAGE = "You analyze the user's conversation and return a list of consecutive words from the following list: ['goToHome', 'goToYellow', 'goToPurple', 'goToRed', 'goToBlue', 'goToGreen', 'getBlock', 'dropBlock' ', 'dance'] It must be included only if it is in the list; For example, 'Go to yellow, pick up the item, come home and love you' return ['goToYellow','getBlock', 'goToHome'], and 'Allez dans la zone jaune et dansez' return ['goToYellow', 'dance']; If you don't understand, return ['dontKnow'], and if you exceed the maxtoken, return ['exceedToken']."
TEMPERATURE = 0.9   # 확률 분포의 엔트로피를 조절합니다. 기본값은 0.7입니다. -> 높을수록 자유로운 답변
MAX_TOKEN = 64      # 생성된 텍스트의 최대 토큰 수를 제한합니다       
TOP_P = 1           # 다음 단어 선택의 확률 분포의 상위 p 퍼센트를 고려합니다.
########################################################################

# 환경 변수 설정
# 혹시 오류나면 절대경로로 수정 필요
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_SPEACH_TO_TEXT_KEY


def record_audio():
    print("Recording started. Press 'q' to stop recording.")
    return subprocess.Popen(["arecord", "--format=S16_LE", "--rate=48000", "--file-type=raw", "out.raw"])

def stop_recording(process):
    print("Recording stopped.")
    process.terminate()
    process.wait()

def get_voice_message(language=LANGUAGE):
    # instantiates a client
    client = speech.SpeechClient()
    # 리퀘스트구성
    config = speech.RecognitionConfig(
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz = 48000,
        language_code = language
    )
    with io.open(LOCAL_FILE_PATH, 'rb') as f:
        content = f.read()
    audio = speech.RecognitionAudio(content=content)
    response = client.recognize(config=config, audio=audio)

    voice_message = ""
    for result in response.results:
        print(f'Transcript: {result.alternatives[0].transcript}')
        voice_message = result.alternatives[0].transcript
    return voice_message

def query_openai_gpt(query, messages=GPT_MESSAGE, temperature=TEMPERATURE, max_token=MAX_TOKEN, top_p = TOP_P):

    openai.api_key = OPENAI_API_KEY     # openai API 키 인증
    model = MODEL             # 모델 - GPT 3.5 Turbo 선택

    # 메시지 설정하기
    messages = [{
        "role": "system",
        "content": GPT_MESSAGE
    }, {
        "role": "user",
        "content": query
    }]

    # ChatGPT API 호출하기
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  
        max_tokens=max_token,    
        top_p=top_p        
    )

    answer = response['choices'][0]['message']['content']
    return answer

def main():

    record_number = 1
    recording_process = None

    while True:
        print("recording number: {}".format(record_number))
        user_input = input("Press 's' to start recording or 'd' to quit: ").strip().lower()
        
        # 음성 시작
        if user_input == 's' and recording_process is None:
            recording_process = record_audio()
            
        # 음성 종료
        elif user_input == 'd' and recording_process is not None:
            stop_recording(recording_process)
            recording_process = None
            record_number += 1

            # 질문 작성하기
            query = get_voice_message()
            gpt_answer = query_openai_gpt(query)
            print("gpt answer:")
            print(gpt_answer)  
        
        # 프로그램 종료
        elif user_input == 'q':
            if recording_process is not None:
                stop_recording(recording_process)
                recording_process = None
            break
        
    
        else:
            print("wrong keyboard input")
    

if __name__ == "__main__":
    main()
