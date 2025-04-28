


from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai using the word scrumptious"}
  ]
)

print(completion.choices[0].message);
