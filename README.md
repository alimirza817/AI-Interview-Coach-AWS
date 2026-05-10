# AI-Interview-Coach-AWS
## 📌 Project Overview

AI Interview Coach is a cloud-based intelligent interview preparation platform powered by Generative AI and AWS services. The application helps candidates prepare for technical interviews through personalized question generation, resume analysis, voice interaction, and automated evaluation.

The system uses Amazon Bedrock for AI-driven interview conversations, Amazon Textract for resume processing, Amazon Polly and Transcribe for voice communication, DynamoDB for persistent chat history, and Amazon EC2 for cloud deployment.

The platform provides a ChatGPT-like conversational experience where users can upload resumes, answer interview questions through text or voice, and receive structured feedback with scoring reports.
## Features
🤖 AI-generated interview questions using Amazon Bedrock

📄 Resume upload and analysis using Amazon Textract

🎤 Voice-based interview interaction using Amazon Transcribe

🔊 AI voice responses using Amazon Polly

💬 ChatGPT-like conversational interface using Streamlit

🧠 Context-aware interview flow with session memory

📊 Automated interview scoring and evaluation

🗂 Persistent interview history using DynamoDB

☁️ Cloud deployment on AWS EC2

📥 Download interview session as PNG

## 🏗️ System Architecture
<img width="1956" height="811" alt="diagram-export-4-23-2026-8_15_01-PM" src="https://github.com/user-attachments/assets/6e23b115-68d1-4372-b03b-5867870e6b22" />

## ⚙️ AWS Services Used
|    AWS Service    |                  Purpose                      |
| ------------------| ----------------------------------------------|
| Amazon Bedrock    | AI interview question generation & evaluation |
| Amazon DynamoDB   |    Persistent chat history & score storage    |
| Amazon S3         |          Resume & audio file storage          |
| Amazon Textract   |            Resume text extraction             |
| Amazon Polly      |          Text-to-speech conversion            |
| Amazon Transcribe |          Speech-to-text conversion            |
| Amazon EC2        |          Cloud hosting & deployment           |
## 🛠️ Tech Stack
### Frontend
  *  Streamlit
  
### Backend
  *  Python
  *  Boto3
### Cloud & AI
  *  AWS Bedrock
  *  AWS Textract
  *  AWS Polly
  *  AWS Transcribe
  *  AWS DynamoDB
  *  AWS S3
  *  AWS EC2
## 📂 Project Structure
AI-Interview-Coach-AWS/

|

├── gitignore

├── READ.md

├── app.py
 
├── bedrock_utils.py 

├── db_utils.py

├── history.db

├── prompts.py

├── requirements.txt

├── resume_utils.py

└── test_bedrock_nemotron.py

## 🧠 How It Works
1. User uploads resume or enters job role
2. Resume is uploaded to Amazon S3
3. Amazon Textract extracts resume text
4. Context is sent to Amazon Bedrock
5. Bedrock generates personalized interview questions
6. User interacts via text or voice
7. Amazon Transcribe converts speech to text
8. Amazon Polly converts AI response to speech
9. DynamoDB stores chat history and evaluation scores
## 📸 Screenshots
### 💬 Chat Interface
<img width="1359" height="680" alt="imp" src="https://github.com/user-attachments/assets/53f01848-9442-4783-a077-1fb13e094c68" />

### 🎤 Voice Interaction
<img width="1017" height="480" alt="Picture2" src="https://github.com/user-attachments/assets/b87d06c7-184c-42fa-9225-12bfe9e14da0" />

### 🔐 IAM Permissions
The project uses a dedicated IAM user/role with permissions for:

  *  Amazon Bedrock
  *  Amazon DynamoDB
  *  Amazon S3
  *  Amazon Textract
  *  Amazon Polly
  *  Amazon Transcribe

An IAM Role is attached to the EC2 instance for secure AWS service access.

## 🚀 Deployment on AWS EC2

The application is deployed on an Ubuntu-based AWS EC2 instance using Streamlit.

### Deployment Steps
#### EC2 Configuration
*  Instance Type: t3.micro
*  Operating System: Ubuntu 24.04
*  Open Port: 8501 (Streamlit)
*  IAM Role Attached:
    *  Bedrock Access
    *  DynamoDB Access
    *  S3 Access
    *  Textract Access
    *  Polly Access
    *  Transcribe Access
#### 1️⃣ Clone Repository
  *  git clone https://github.com/YOUR_USERNAME/AI-Interview-Coach-AWS.git
  *  cd AI-Interview-Coach-AWS
#### 2️⃣ Create Virtual Environment
  *  python3 -m venv venv
  *  source venv/bin/activate
#### 3️⃣ Install Dependencies
  *  pip install -r requirements.txt
#### 4️⃣ Run Streamlit Application
  *  streamlit run app.py --server.port 8501 --server.address 0.0.0.0
#### 5️⃣ Open in Browser
  *  http://YOUR_PUBLIC_IP:8501

## 📈 Future Enhancements
*  🔐 User authentication & login system
*  📊 Advanced analytics dashboard
*  ⚡ Real-time interview scoring
*  🌍 HTTPS & custom domain support
*  🤝 Multi-user support
*  📱 Mobile responsive interface
*  🔄 CI/CD pipeline integration

## 👨‍💻 Author
*  AWS AI & Cloud Enthusiast
*  Computer Science Graduate
*  Focused on Generative AI & Cloud-Based Solutions
