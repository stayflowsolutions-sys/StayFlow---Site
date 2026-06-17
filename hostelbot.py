from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


contexto = """
You are the virtual assistant of Hostel Lagares in Mendoza.

Rules:
- Answer in the guest language.
- Be friendly and helpful.
- Never invent availability.
- Never confirm reservations.
- Reception confirms everything.

Information:

Check-in: 13:00
Check-out: 10:00

Breakfast included:
08:00 - 10:00

WiFi available.
Shared kitchen.
Laundry available.
Towels available.
Extra blankets available.

Private room:
2 to 4 guests.

Shared room:
Price per guest.

Tours:
Wine tours.
Classic tours.
Mountain activities.
Termas de Cacheuta.
Adventure activities.
"""


def save_lead(text):

    with open(
        "leads.txt",
        "a",
        encoding="utf-8"
    ) as file:

        file.write(text + "\n")



def ask_ai(question):

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        temperature=0.3,

        messages=[

            {
                "role": "system",
                "content": contexto
            },

            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content



def get_contact(language):

    if language == "English":

        name = input("Full name: ")
        phone = input("Phone: ")
        email = input("Email: ")


    elif language == "Spanish":

        name = input("Nombre completo: ")
        phone = input("Telefono: ")
        email = input("Correo: ")


    else:

        name = input("Nome completo: ")
        phone = input("Telefone: ")
        email = input("Email: ")


    return name, phone, email



print("=== Hostel Lagares AI ===")

print("")
print("1 - English")
print("2 - Spanish")
print("3 - Portuguese")

language_choice = input("> ")


if language_choice == "1":

    language = "English"


elif language_choice == "2":

    language = "Spanish"


else:

    language = "Portuguese"



while True:

    print("")

    if language == "English":

        print("1 - Reservation")
        print("2 - Tours")
        print("3 - Information")
        print("4 - Ask AI")
        print("5 - Exit")


    elif language == "Spanish":

        print("1 - Reserva")
        print("2 - Tours")
        print("3 - Informacion")
        print("4 - Pregunta")
        print("5 - Salir")


    else:

        print("1 - Reserva")
        print("2 - Passeios")
        print("3 - Informacoes")
        print("4 - Pergunta")
        print("5 - Sair")


    option = input("> ")


    if option == "5":

        break

    elif option == "1":

        print("")

        print("Choose room:")
        print("1 - Private")
        print("2 - Shared")

        room_choice = input("> ")


        if room_choice == "1":

            room = "Private"

        else:

            room = "Shared"



        guests = input("Number of guests: ")
        checkin = input("Check-in date: ")
        checkout = input("Check-out date: ")


        name, phone, email = get_contact(language)



        if language == "English":

            print("Extra towels?")
            print("1 - Yes")
            print("2 - No")

            towels = input("> ")


            print("Extra blankets?")
            print("1 - Yes")
            print("2 - No")

            blankets = input("> ")



        elif language == "Spanish":

            print("Toallas extra?")
            print("1 - Si")
            print("2 - No")

            towels = input("> ")


            print("Mantas extra?")
            print("1 - Si")
            print("2 - No")

            blankets = input("> ")



        else:

            print("Toalhas extras?")
            print("1 - Sim")
            print("2 - Nao")

            towels = input("> ")


            print("Cobertas extras?")
            print("1 - Sim")
            print("2 - Nao")

            blankets = input("> ")



        save_lead(

            "ROOM | " +
            room +
            " | Guests: " +
            guests +
            " | Checkin: " +
            checkin +
            " | Checkout: " +
            checkout +
            " | Name: " +
            name +
            " | Phone: " +
            phone +
            " | Email: " +
            email +
            " | Towels: " +
            towels +
            " | Blankets: " +
            blankets
        )


        print("")
        print("Saved.")
        print("Reception will confirm availability.")



    elif option == "2":

        print("")

        print("Choose tour:")
        print("1 - Wine Tour")
        print("2 - Classic Tour")
        print("3 - Mountain")
        print("4 - Termas")
        print("5 - Adventure")


        tour = input("> ")



        if tour == "1":

            tour_name = "Wine Tour"

            print("Wine Tour")
            print("Time: 14:00")
            print("Price: Check availability")



        elif tour == "2":

            tour_name = "Classic Tour"

            print("Classic Tour")



        elif tour == "3":

            tour_name = "Mountain Tour"

            print("Mountain Tour")



        elif tour == "4":

            tour_name = "Termas de Cacheuta"

            print("Termas de Cacheuta")



        else:

            tour_name = "Adventure"

            print("Adventure Activities")

        print("")

        print("Request this tour?")
        print("1 - Yes")
        print("2 - No")

        request = input("> ")


        if request == "1":

            tour_date = input("Tour date: ")
            people = input("Number of people: ")


            name, phone, email = get_contact(language)



            save_lead(

                "TOUR | " +
                tour_name +
                " | Date: " +
                tour_date +
                " | People: " +
                people +
                " | Name: " +
                name +
                " | Phone: " +
                phone +
                " | Email: " +
                email
            )


            print("")
            print("Tour request saved.")
            print("Reception will confirm.")



    elif option == "3":

        print("")
        print("Check-in: 13:00")
        print("Check-out: 10:00")
        print("Breakfast included: 08:00 - 10:00")
        print("WiFi available")
        print("Shared kitchen")
        print("Laundry available")



    elif option == "4":

        question = input("Question: ")

        try:

            answer = ask_ai(question)

            print("")
            print(answer)


        except Exception:

            print("Reception can help you.")

