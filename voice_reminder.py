
import streamlit as st
import speech_recognition as sr
import pygame
import dateparser
from datetime import datetime, timedelta
import time
import threading
import os
import re

# 初始化播放器
if not pygame.mixer.get_init():
    pygame.mixer.init()

if not os.path.exists("voice_files"):
    os.makedirs("voice_files")

if "reminders" not in st.session_state:
    st.session_state.reminders = []

def system_speak(text):
    """機器發出引導聲音"""
    try:
        import platform
        if platform.system() == "Windows":
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
        elif platform.system() == "Darwin":
            os.system(f'say "{text}"')
        else:
            st.warning(f"系統語音：{text}")
    except Exception as e:
        st.warning(f"改用文字顯示：{text}")

def listen_voice_segment(prompt_text):
    """引導語音輸入"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"🎤 聆聽中... {prompt_text}")
        r.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            st.success("接收成功，解析中...")
            text = r.recognize_google(audio, language="zh-TW")
            return text, audio
        except Exception as e:
            return None, None

def play_my_voice(file_path):
    """準時播放你錄下的第一階段原音"""
    try:
        if os.path.exists(file_path):
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
    except Exception as e:
        st.error(f"原音播放失敗: {e}")

def check_reminders():
    while True:
        now = datetime.now()
        for reminder in st.session_state.reminders:
            if not reminder["triggered"] and now >= reminder["notify_time"]:
                reminder["triggered"] = True
                play_my_voice(reminder["audio_path"])
        time.sleep(1)

if "bg_thread" not in st.session_state:
    t = threading.Thread(target=check_reminders, daemon=True)
    t.start()
    st.session_state.bg_thread = True

# --- 乾淨的 UI 介面 ---
st.title("🎙️ 一問一答語音防忘助手")
st.write("點擊下方按鈕啟動，跟著機器的引導說話即可。")

if st.button("🚀 啟動全語音對話", use_container_width=True):
    reminder_id = int(time.time())
    
    # ─── 第一步：問事情 ───
    system_speak("請問有什麼事情要記錄的嗎？")
    event_text, event_audio = listen_voice_segment("請說出要記錄的事項與時間（例如：10月20號要去修車）")
    
    if event_text and event_audio:
        st.write(f"🗣️ 記錄事項：**{event_text}**")
        
        # 存下這段最純粹的原音（完全沒有後面提醒時間的雜音）
        audio_path = f"voice_files/event_{reminder_id}.wav"
        with open(audio_path, "wb") as f:
            f.write(event_audio.get_wav_data())
            
        # ─── 第二步：問何時提醒 ───
        time.sleep(0.5)
        system_speak("好的，請問希望什麼時候提醒你呢？")
        time_text, _ = listen_voice_segment("請說出提醒時機（例如：一天前、前十分鐘、準時）")
        
        if time_text:
            st.write(f"🗣️ 提醒時機：**{time_text}**")
            
            # ─── 第三步：解析時間 ───
            event_time = dateparser.parse(event_text, languages=['zh'], settings={'PREFER_DATES_FROM': 'future'})
            
            if event_time:
                config_type = "exactly"
                if "前十分鐘" in time_text or "10分鐘" in time_text or "十分鐘" in time_text:
                    notify_time = event_time - timedelta(minutes=10)
                elif "前三十分鐘" in time_text or "30分鐘" in time_text or "三十分鐘" in time_text:
                    notify_time = event_time - timedelta(minutes=30)
                elif "一天前" in time_text or "前一天" in time_text:
                    notify_time = event_time - timedelta(days=1)
                else:
                    notify_time = event_time
                
                # 存入排程
                st.session_state.reminders.append({
                    "event_time": event_time,
                    "notify_time": notify_time,
                    "text": event_text,
                    "audio_path": audio_path,
                    "triggered": False
                })
                
                st.success("🎉 語音排程設定成功！")
                system_speak("好的，沒問題，已經幫您記住了。")
            else:
                st.error("無法解析出具體日期，請重新啟動並說清楚日期（如10月20號）。")
                if os.path.exists(audio_path): os.remove(audio_path)
        else:
            st.error("第二階段沒有收到您的聲音，設定失敗。")
            if os.path.exists(audio_path): os.remove(audio_path)
    else:
        st.error("第一階段沒有收到您的聲音，設定失敗。")

st.markdown("---")
st.subheader("📋 目前的原音排程清單")
if st.session_state.reminders:
    for rem in st.session_state.reminders:
        status = "✅ 已播放" if rem["triggered"] else "⏳ 監控中"
        st.write(f"**[{status}]** 播音時間：{rem['notify_time'].strftime('%m-%d %H:%M')} ── 內容：『{rem['text']}』")
else:
    st.write("目前沒有任何排程。")
