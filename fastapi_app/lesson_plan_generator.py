import openai
import json
import re
from difflib import get_close_matches
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class LessonPlanGenerator:
    def __init__(self):
        self.class_number = None
        self.subject = None
        self.learning_outcome = None
        self.state = 'greeting'
        self.lesson_plans = None
        self.current_question = None
        self.principles = '''
        Integrity- Always act with courage, respect, and toleration.
        Opportunity- Approach everything in life as a reason to improve; recognize and seize what life has to offer.
        Win-Win Focus- Cooperation creates real value in society-for yourself and others.
        Sound Judgement- Use economic thinking to create the greatest benefit with the least resources.
        Knowledge- Seek and use the best knowledge, drive change that benefits others, and exemplify humility and intellectual honesty.
        Passion- Find fulfillment in your life by improving the lives of others.
        Freedom- Respect the rights of others and study the links between freedom, entrepreneurship, and societal well-being.
        Responsibility- Take responsibility for your own life. No one will ever be as concerned about your success as you.
        '''
        self.market_concepts = '''
        comparative advantage, sunk cost, scarcity, growth mindset, Opportunity cost, subjective value
        '''
        self.valid_outcomes = self.extract_valid_outcomes()
        self.openai_api_key = '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'
        openai.api_key = self.openai_api_key

    def gpt_call(self, system_prompt, user_prompt, model="gpt-4"):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in GPT call: {e}")
            return None

    def extract_valid_outcomes(self):
        outcomes = []
        principle_names = re.findall(r'^(\w+(?:-\w+)?)-', self.principles, re.MULTILINE)
        outcomes.extend(principle_names)
        
        key_phrases = re.findall(r'(?:^|\. )([^.]+?(?:improve|create|benefit|change|respect|study|responsibility)[^.]+)\.', self.principles)
        outcomes.extend(key_phrases)
        
        outcomes.extend([concept.strip() for concept in self.market_concepts.split(',')])
        
        return outcomes

    def classify_intent(self, user_input):
        intent_dict = {
            "greeting": [
                "Hello",
                "Hi there",
                "Hey",
                "Good morning",
                "Good afternoon"
            ],
            "provide_class": [
                "I teach 6th grade",
                "It's for 8th grade students",
                "The class is 3rd grade"
            ],
            "provide_subject": [
                "I'm teaching math",
                "The subject is science",
                "It's for an English class"
            ],
            "provide_learning_outcome": [
                "I want to focus on responsibility",
                "The learning outcome is comparative advantage",
                "We're learning about growth mindset"
            ],
            "request_help": [
                "I'm not sure what to enter",
                "Can you give me some suggestions?",
                "What should I say?"
            ],
            "choose_lesson_plan": [
                "I'd like to see the first plan",
                "Let's go with lesson plan 2",
                "Number 3 sounds interesting"
            ],
            "irrelevant_question": [
                "What's the weather like today?",
                "Who won the last World Cup?",
                "Tell me about the solar system"
            ]
        }

        system_prompt = "You are an AI assistant tasked with classifying user intents in a lesson plan generation context."
        user_prompt = "Here are some example intents and corresponding user inputs:\n\n"

        for intent, examples in intent_dict.items():
            user_prompt += f"Intent: {intent}\n"
            for example in examples:
                user_prompt += f"User input: {example}\n"
            user_prompt += "\n"

        user_prompt += f"Now, classify the following user input:\n{user_input}\n\nIntent:"

        response = self.gpt_call(system_prompt, user_prompt)
        return response.strip()

    def handle_user_input(self, user_input):
        user_input = user_input.strip().lower()

        intent = self.classify_intent(user_input)

        if intent == "greeting":
            if self.state == 'greeting':
                self.state = 'collect_info'
                return "Hello! I'm here to help you create a lesson plan. " + self.get_next_question()
            else:
                return "Hello again! " + self.get_current_question()

        if intent == "request_help":
            return self.provide_help()

        if intent == "irrelevant_question":
            return f"I'm here to help you create lesson plans. {self.get_current_question()}"

        if self.state == 'greeting':
            self.state = 'collect_info'

        if self.state == 'collect_info':
            extracted_class = self.extract_class_number(user_input)
            extracted_subject = self.extract_subject(user_input)
            extracted_outcome = self.extract_learning_outcome(user_input)

            if extracted_class:
                self.class_number = extracted_class
            if extracted_subject:
                self.subject = extracted_subject
            if extracted_outcome:
                self.learning_outcome = extracted_outcome

            return self.get_next_question()

        if self.state == 'choose_plan':
            return self.handle_lesson_plan_choice(user_input)

        return "I didn't understand that. Let's start over. What class are you teaching?"

    def get_next_question(self):
        if not self.class_number:
            return "What class are you teaching? For example, '6th grade' or just '6'."
        elif not self.subject:
            return f"What subject are you teaching to your {self.class_number} students?"
        elif not self.learning_outcome:
            suggestions = ", ".join(self.valid_outcomes[:5])
            return f"What's the learning outcome? You could choose from these suggestions: {suggestions}, or provide your own."
        else:
            self.state = 'generate_plans'
            return self.generate_lesson_plans()

    def get_current_question(self):
        return self.get_next_question()

    def extract_class_number(self, user_input):
        word_to_num = {'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10', 'eleventh': '11', 'twelfth': '12'}
        
        for word, num in word_to_num.items():
            if word in user_input:
                return f"{num}th grade"
        
        match = re.search(r'\d+', user_input)
        if match:
            return f"{match.group()}th grade"
        
        return None

    def extract_subject(self, user_input):
        subjects = ['math', 'mathematics', 'english', 'science', 'history', 'geography', 'art', 'music', 'physical education', 'pe', 'computer science', 'biology', 'chemistry', 'physics', 'literature', 'social studies']
        
        for subject in subjects:
            if subject in user_input:
                return subject.capitalize()
        
        return None

    def extract_learning_outcome(self, user_input):
        user_input = user_input.lower()
        
        for outcome in self.valid_outcomes:
            if outcome.lower() in user_input:
                return outcome

        words = user_input.split()
        for i in range(len(words)):
            for j in range(i+1, len(words)+1):
                phrase = ' '.join(words[i:j])
                close_matches = get_close_matches(phrase, self.valid_outcomes, n=1, cutoff=0.6)
                if close_matches:
                    return close_matches[0]

        return None

    def provide_help(self):
        if not self.class_number:
            return "For the class, you can enter a grade level like '6th grade' or just the number, such as '6'."
        elif not self.subject:
            return f"For the subject, you can enter any standard school subject like 'Math', 'Science', 'English', 'History', etc."
        elif not self.learning_outcome:
            suggestions = ", ".join(self.valid_outcomes[:5])
            return f"For the learning outcome, try to relate it to one of our principles or market concepts. Some examples are: {suggestions}. You can also describe a specific skill or knowledge you want your students to gain."
        else:
            return "I have all the information I need. Let me generate the lesson plans for you."

    def generate_lesson_plans(self):
        system_prompt = "You are an experienced teacher tasked with creating engaging lesson plans."
        user_prompt = f"""
        Create 3 lesson plans for a {self.class_number} {self.subject} class with the learning outcome: {self.learning_outcome}.
        Each lesson plan should include:
        1. A title
        2. An objective
        3. A detailed activity description
        4. Debrief questions
        5. Relevant principles and market concepts (e.g., Opportunity, Responsibility, Sound Judgement, Growth Mindset, Win-Win Focus, Sunk Cost, Scarcity)

        Format the response as a narrative, similar to this:

        Wonderful! Let's focus on [learning outcome] in your [subject] class. Here are three lesson plans designed to help your students [achieve goal] while connecting to real-world relevancy and incorporating Empowered's principles.

        **Lesson Plan 1: [Title]**
        **Objective:** [Objective description]
        **Activity:**
        1. [Step 1]
        2. [Step 2]
        3. [Step 3]
        **Debrief Questions:**
        1. [Question 1]
        2. [Question 2]
        3. [Question 3]
        **Principles and Market Concepts:**
        * **[Principle 1]:** [How it applies]
        * **[Principle 2]:** [How it applies]
        * **[Principle 3]:** [How it applies]
        * **[Principle 4]:** [How it applies]

        [Repeat for Lesson Plan 2 and Lesson Plan 3]

        **Next Steps**
        Which lesson plan are you most interested in trying with your students?

        Ensure the activities are engaging, age-appropriate, and aligned with the learning outcome.
        """
        response = self.gpt_call(system_prompt, user_prompt)
        self.lesson_plans = response
        self.state = 'choose_plan'
        return response + "\n\nWhich lesson plan would you like me to elaborate on? Please choose 1, 2, or 3."

    def handle_lesson_plan_choice(self, user_input):
        try:
            plan_number = int(''.join(filter(str.isdigit, user_input)))
            if 1 <= plan_number <= 3:
                return self.elaborate_lesson_plan(self.lesson_plans[plan_number - 1])
            else:
                return "Please choose a number between 1 and 3 for the lesson plan you want to explore."
        except ValueError:
            return "I didn't understand that. Please specify which lesson plan (1, 2, or 3) you'd like to explore in more detail."

    def elaborate_lesson_plan(self, lesson_plan):
        system_prompt = "You are an experienced teacher providing additional details for a lesson plan."
        user_prompt = f"""
        Please elaborate on the following lesson plan by providing:
        1. Detailed supplies needed
        2. Assessment opportunities
        3. Pro tips for implementation

        Lesson plan:
        {lesson_plan}

        Format the response as:

        **Supplies Needed:**
        * [Supply 1]
        * [Supply 2]
        * [Supply 3]

        **Assessment Opportunities:**
        * [Assessment 1]
        * [Assessment 2]

        **Pro Tips:**
        * [Tip 1]
        * [Tip 2]
        * [Tip 3]

        I'm excited to hear how this lesson goes in your classroom!
        """
        return self.gpt_call(system_prompt, user_prompt)

# FastAPI setup
app = FastAPI()

class UserInput(BaseModel):
    content: str

@app.post("/chat")
async def chat(user_input: UserInput):
    generator = LessonPlanGenerator()
    response = generator.handle_user_input(user_input.content)
    return {"response": response}
