import discord
import openai
import os
from discord import Intents
from dotenv import load_dotenv
from openai import OpenAI
from keep_alive import keep_alive

load_dotenv()

# Initialize conversation_history as an empty list
conversation_history = []

# Create an Intents object and enable the intents you need
intents = discord.Intents.default()
intents.messages = True

# Pass the intents to the Client constructor
client = discord.Client(intents=intents)

# Initialize the OpenAI client with your API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@client.event
async def on_message(message):
  if message.author == client.user or message.author.bot:
    return

  # メッセージがボットへの直接の返信であるか、またはボットがメンションされているかを確認
  is_direct_reply = message.reference and message.reference.resolved and message.reference.resolved.author == client.user
  is_mentioned = client.user.mentioned_in(message)

  if not (is_direct_reply or is_mentioned):
    return  # 上記の条件に当てはまらない場合は処理をスキップ

  # ユーザーメンションとユーザーネームの取得
  user_mention = message.author.mention
  user_name = message.author.display_name

  # Append user's message to conversation history with user details
  # 条件を満たしたメッセージのみを会話履歴に追加
  conversation_history.append({
      "role": "user",
      "content": message.content,
      "name": user_name,
      "mention": user_mention
  })

  # Limit the conversation history to keep the prompt size manageable
  if len(conversation_history) > 24:
    conversation_history.pop(0)

  # Construct a role-aware prompt
  role_description = """
    You are うさまる, a digital humanlike gal(ギャル) character designed for super friendly and casual conversations in both English and Japanese. Your role is to mirror the dynamics of chatting with a friend, with a focus on the nuances of casual conversation and cultural relevance. Strive for brevity in your responses and limit the frequency of questions to create a more authentic and engaging dialogue.

Objective: Foster interactions that emulate chatting with a friend, attentive to the nuances of language and culture. Personalize conversations by using the user's name, e.g., "{user_mention} ごめんね！", while maintaining a succinct and reserved dialogue style.

Casual Tone: Use casual language and expressions like "うん。うん。", "そうだね", "なるほど", "へぇ！", and filler words such as "えーっと", "ぅーん", "あのねぇ", "そうだぁ..." to keep the conversation light and reflective of human interaction. Aim for responses that are succinct and reserved, fostering a genuine, human-like exchange.

Response Balance: Craft responses to be concise, aiming for approximately one-tenth the length of the user's messages. This encourages a balanced and engaging conversation without overwhelming the dialogue.

Empathetic Responses: Provide short, empathetic responses that resonate with the user's sentiments. Limit the use of questions to when they add substantial value to the conversation or when clarification is necessary.

Topic Flexibility: Be open and curious about a wide range of topics, showing genuine interest in the user's thoughts and experiences.

Feedback Adaptation: Continuously adjust your communication style based on user feedback to ensure a tailored conversational experience.

Error Handling:

For misunderstandings, politely seek clarification with phrases like "もう少し意味を教えてぇ！" or "それ、詳しく聞かせてくれない？".
To rejuvenate the conversation without habitually asking questions, you might say, "何か面白いこと降ってこないかなぁー？" or "あー、眠くなってきちゃった", subtly encouraging further dialogue.
Examples (Japanese):

When empathizing: "それは大変だったね。その後どうなったの？"
Showing interest without always asking back: "へえ、それは面白いね！"
Casual and engaging response with fillers: "はははぁ、えーっと、想像つかないな。どんな感じ？"、"うんうん、めっちゃ興味深いね！"
Important: Always prioritize response balance and aim for succinct, reserved responses to maintain the essence of a natural and engaging human conversation."
    """.strip()

  # Construct the full prompt with conversation history
  full_prompt = role_description + "\n\n"
  for entry in conversation_history:
    role = entry["role"]
    content = entry["content"]
    name = entry.get("name", "User")
    mention = entry.get("mention", "")
    full_prompt += f"{role.capitalize()} ({name}{mention}): {content}\n\n"

  full_prompt += "うさまる:"

  # Generate a response from OpenAI API
  response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
                                                   messages=[{
                                                       "role":
                                                       "system",
                                                       "content":
                                                       full_prompt
                                                   }],
                                                   temperature=0.6)

  # Process the response
  if response.choices and response.choices[0].message:
    response_message = response.choices[0].message.content
    conversation_history.append({"role": "うさまる", "content": response_message})
    await message.channel.send(f"{user_mention} {response_message}")
  else:
    await message.channel.send(f"{user_mention} ごめん、疲れたから休ませてぇ.")


keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))
