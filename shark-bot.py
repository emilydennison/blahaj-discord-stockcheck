import json
import colorama
import requests
from discord import webhook
from discord import embeds
import datetime

webhookURL = " "

with open("stores.json") as f:
    # Parsed from (search for "allStores=["):
    # https://www.ikea.com/gb/en/products/javascripts/range-stockcheck.ebfce6584a37458deef3.js
    stores = json.load(f)


def calculate_stock(availability):
    store_id = availability["classUnitKey"]["classUnitCode"]
    store_name = \
        [store["name"] for store in stores if store["value"] == store_id]
    if len(store_name) < 1:
        return None

    store_name = store_name[0]
    if list(availability["buyingOption"]["cashCarry"].keys())[0] == "range":
        return {
            "store": store_name,
            "quantity": 0,
            "next_restock": None,
        }
    availability_info = availability["buyingOption"]["cashCarry"]["availability"]
    quantity = int(availability_info["quantity"])

    next_restock = None
    if "restocks" in availability_info:
        next_restock = availability_info["restocks"][0]

    return {
        "store": store_name,
        "quantity": quantity,
        "next_restock": next_restock,
    }


def pretty_print_stock(stock):
    store = stock["store"]
    quantity = stock["quantity"]
    next_restock = stock["next_restock"]

    s = ""
    if quantity > 0:
        s += colorama.Fore.GREEN
    else:
        s += colorama.Fore.RED
    s += store
    s += colorama.Fore.RESET
    s += " "
    s += str(quantity)

    if next_restock is not None:
        s += colorama.Fore.LIGHTBLACK_EX
        s += " (restock of "
        s += colorama.Fore.RESET
        s += str(next_restock["quantity"])
        s += colorama.Fore.LIGHTBLACK_EX
        s += " coming "
        s += colorama.Fore.RESET
        s += next_restock["earliestDate"]
        s += " ~ "
        s += next_restock["latestDate"]
        s += colorama.Fore.LIGHTBLACK_EX
        s += ")"
        s += colorama.Fore.RESET

    print(s)


def main():
    colorama.init()
    for maybeShonk  in range(1, 3):
        if maybeShonk == 1:
            shorkType = "30373588"
            shorkName = "Bighåj"
        elif maybeShonk == 2:
            shorkType = "20540663"
            shorkName = "Smolhåj"
        print("Fetching " + shorkName + " listings…\n")

        bigAvailabilities = requests.get("https://api.ingka.ikea.com/cia/availabilities/ru/gb?itemNos=" + shorkType + "&expand=StoresList,Restocks,SalesLocations", headers={
            "Accept": "application/json;version=2",
            "X-Client-ID": "b6c117e5-ae61-4ef5-b4cc-e0b1e37f0631"
        })
        bigAvailabilities = bigAvailabilities.json()
        sharks = []
        for availability in bigAvailabilities["availabilities"]:
            stock = calculate_stock(availability)
            if stock is None:
                continue
            sharks.append(stock)
        sharks.sort(key=lambda s: s["quantity"], reverse=True)

        for stock in sharks:
            pretty_print_stock(stock)
        send_webhook(sharks, shorkName)


def send_webhook(sharks, shorkName):
    hook = webhook.SyncWebhook.from_url(
        webhookURL)
    messageEmbeds = [
        embeds.Embed(
            title="Blåhaj stock in the UK",\
            description="Here is " + shorkName + " stock for today in the UK.",\
            url="https://www.ikea.com/gb/en/p/blahaj-soft-toy-shark-30373588/",\
            colour=0x6996AD,\
            timestamp=datetime.datetime.today(),
        )

    ]
    messageEmbeds[0].set_footer(text = "shonk")
    messageEmbeds[0].set_thumbnail(url="https://www.ikea.com/gb/en/images/products/blahaj-soft-toy-shark__0877368_pe633607_s5.jpg")
    messageEmbeds[0].set_author(name = "a sentient blåhaj")

    # Break up the message into two chunks (Character limit in Discord embeds cmomplains otherwise) 
    sharks1 = sharks[:len(sharks)//2]
    sharks2 = sharks[len(sharks)//2:]
    rows1 = []
    rows2 = []
    for shark in sharks1:
        if shark["next_restock"] == None:
            rows1.append(shark["store"] + ": " + str(shark["quantity"]))
        else:
            rows1.append(shark["store"] + ": " + str(shark["quantity"] + ". Restock due: " + str(shark["next_restock"]["latestDate"])))
    for shark in sharks2:
        if shark["next_restock"] == None:
            rows2.append(shark["store"] + ": " + str(shark["quantity"]))
        else:
            rows2.append(shark["store"] + ": " + str(shark["quantity"]) + ". Restock due: " + str(shark["next_restock"]["latestDate"]))
    # Print each item in the list as its own line. 
    messageEmbeds[0].add_field(name="Stock:", value="\n".join(rows1), inline=True)
    messageEmbeds[0].add_field(name="Further stock:", value="\n".join(rows2), inline=True)

    hook.send(content="", username="shark-alert-bot", embeds=messageEmbeds)


main()
