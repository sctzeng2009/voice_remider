import streamlit as st
from streamlit_mic_recorder import mic_recorder
import dateparser
from datetime import datetime, timedelta

if "reminders" not in st.session_state:
    st.session_state.reminders = []

st.title("🎙️ 智慧網頁語音防忘助手")
st.write("請允許瀏覽器使用麥克風。錄音完畢後，時間到時網頁會自動播放您的原音。")

st.markdown("### 📥 第一步：請錄下您要記錄的事情")
st.write("💡 範例：點擊下方按鈕，對著麥克風說『10月20號要去修車』")

event_audio = mic_recorder(
    start_prompt="🔴 開始錄製事情",
    stop_prompt="⏹️ 錄音結束",
    key="event_mic"
)

if event_audio:
    audio_bytes = event_audio['bytes']
    st.audio(audio_bytes, format='audio/wav') 

    st.markdown("---")
    st.markdown("### 📅 第二步：請設定您希望什麼時候提醒")

    time_config = st.radio(
        "請選擇提醒時機：",
        ["準時提醒", "提前 10 分鐘", "提前 30 分鐘", "一天前"]
    )

    text_input = st.text_input("✍️ 請簡單輸入您剛才說的日期時間（例如：10月20日 15:00）：")

    if st.button("✅ 確認送出排程", use_container_width=True):
        if text_input:
            event_time = dateparser.parse(text_input, languages=['zh'], settings={'PREFER_DATES_FROM': 'future'})
            if event_time:
                if time_config == "提前 10 分鐘":
                    notify_time = event_time - timedelta(minutes=10)
                elif time_config == "提前 30 分鐘":
                    notify_time = event_time - timedelta(minutes=30)
                elif time_config == "一天前":
                    notify_time = event_time - timedelta(days=1)
                else:
                    notify_time = event_time

                st.session_state.reminders.append({
                    "event_time": event_time,
                    "notify_time": notify_time,
                    "audio_bytes": audio_bytes,
                    "triggered": False
                })
