#!/bin/bash

# Combine all sections into API_GUIDE.md
cat do_not_edit.md > API_GUIDE.md

cat sections/00_header.md >> API_GUIDE.md

cat sections/01_voice_agent.md >> API_GUIDE.md
cat sections/02_agent_task.md >> API_GUIDE.md
cat sections/03_worker.md >> API_GUIDE.md
cat sections/04_vad.md >> API_GUIDE.md
cat sections/05_llm.md >> API_GUIDE.md
cat sections/06_chat_context.md >> API_GUIDE.md
cat sections/07_fallback_adapters.md >> API_GUIDE.md
cat sections/08_audio_recognition.md >> API_GUIDE.md
cat sections/09_stt.md >> API_GUIDE.md
cat sections/10_tts.md >> API_GUIDE.md
cat sections/11_performance_monitoring.md >> API_GUIDE.md


cat sections/99_footer.md >> API_GUIDE.md

# Update relative links
sed -i '' 's/\.md//g' API_GUIDE.md 


echo -e "Now run 'python bin/create_toc.py' to update the TOC"


