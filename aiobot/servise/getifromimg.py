import base64
from g4f.client import Client



async def ai_analyze_category(file_id, bot, options: str) -> str:
    file_path = f"temp_{file_id}.jpg"
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, file_path)

        client = Client()
        with open(file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = (
            f"Анализируй фото товара. Выбери наиболее подходящую категорию ТОЛЬКО из этого списка: {options}. "
            "В ответе напиши только одно выбранное слово, без знаков препинания и пояснений. "
            "Если сомневаешься, напиши первое слово из списка."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt, "image": encoded_image}]
        )
        
        result = response.choices[0].message.content.strip().replace(".", "").capitalize()
        return result
    except Exception as e:
        print(f"AI Error: {e}")
        return "Одежда"
    finally:
        import os
        if os.path.exists(file_path):
            os.remove(file_path)