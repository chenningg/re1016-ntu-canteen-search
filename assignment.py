import pygame
from PIL import Image
import time
import pandas as pd
import os
import re # For string slicing stuff (used in natural sort function)
import difflib # For string matching in keywords for keyword suggestions and matching

# Center any windows opened (the map, for example)
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Load dataset for keyword dictionary
def load_stall_keywords(data_location="canteens.xlsx"):
    # Get list of canteens and stalls
    canteen_data = pd.read_excel(data_location, trim_ws=True)
    canteens = canteen_data['Canteen'].unique()
    canteens = sorted(canteens, key=str.lower)

    stalls = canteen_data['Stall'].unique()
    stalls = sorted(stalls, key=str.lower)

    keywords = {}
    for canteen in canteens:
        keywords[canteen] = {}

    copy = canteen_data.copy()
    copy.drop_duplicates(subset="Stall", inplace=True)
    stall_keywords_intermediate = copy.set_index('Stall')['Keywords'].to_dict()
    stall_canteen_intermediate = copy.set_index('Stall')['Canteen'].to_dict()

    for stall in stalls:
        stall_keywords = stall_keywords_intermediate[stall]
        stall_canteen = stall_canteen_intermediate[stall]
        keywords[stall_canteen][stall] = stall_keywords

    return keywords


# Load dataset for price dictionary
def load_stall_prices(data_location="canteens.xlsx"):
    # Get list of canteens and stalls
    canteen_data = pd.read_excel(data_location, trim_ws=True)
    canteens = canteen_data['Canteen'].unique()
    canteens = sorted(canteens, key=str.lower)

    stalls = canteen_data['Stall'].unique()
    stalls = sorted(stalls, key=str.lower)

    prices = {}
    for canteen in canteens:
        prices[canteen] = {}

    copy = canteen_data.copy()
    copy.drop_duplicates(subset="Stall", inplace=True)
    stall_prices_intermediate = copy.set_index('Stall')['Price'].to_dict()
    stall_canteen_intermediate = copy.set_index('Stall')['Canteen'].to_dict()

    for stall in stalls:
        stall_price = stall_prices_intermediate[stall]
        stall_canteen = stall_canteen_intermediate[stall]
        prices[stall_canteen][stall] = stall_price

    return prices


# Load dataset for location dictionary
def load_canteen_location(data_location="canteens.xlsx"):
    # Get list of canteens
    canteen_data = pd.read_excel(data_location, trim_ws=True)
    canteens = canteen_data['Canteen'].unique()
    canteens = sorted(canteens, key=str.lower)

    # Get dictionary of {canteen:[x,y]}
    canteen_locations = {}
    for canteen in canteens:
        copy = canteen_data.copy()
        copy.drop_duplicates(subset="Canteen", inplace=True)
        canteen_locations_intermediate = copy.set_index('Canteen')['Location'].to_dict()
    for canteen in canteens:
        canteen_locations[canteen] = [int(canteen_locations_intermediate[canteen].split(',')[0]),
                                      int(canteen_locations_intermediate[canteen].split(',')[1])]

    return canteen_locations


# Get user's location with the use of PyGame
def get_user_location_interface():
    # Initialize pygame
    pygame.init()
    
    # Get dimensions and files
    imageLocation = 'NTUcampus.jpg'
    pinLocation = 'pin.png'
    screenTitle = "Location Based Search (NTU)"
    mapSize = (620, 750)
    pinSize = (50, 50)
    
    # Set screen width and height for display surface
    screen = pygame.display.set_mode(mapSize)

    # Set title of screen
    pygame.display.set_caption(screenTitle)

    # Open image file and pin file, and scale them to the desired size
    ntuMapOriginal = pygame.image.load(imageLocation).convert()
    ntuMap = pygame.transform.smoothscale(ntuMapOriginal, mapSize)
    pinOriginal = pygame.image.load(pinLocation).convert_alpha()
    pin = pygame.transform.smoothscale(pinOriginal, pinSize)

    # Loop for the whole interface while it remains active
    exit = False
    userLocation = None
    while not exit:
        # First, we make a call to the event queue to check for events every frame
        for event in pygame.event.get():
            # User exits the window, we return an error as location was not selected
            if event.type == pygame.QUIT:
                exit = True
                userLocation = None

            # DISPLAY ELEMENTS
            # If the window is not closed, then we show NTU map and let the user pick a location
            screen.blit(ntuMap, (0,0))

            # Do NOT allow resizing of window
            """ # If the user resizes the window, resize accordingly
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.dict['size'], pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                screen.blit(pygame.transform.smoothscale(screen, event.dict['size']), (0, 0))
                scaledHeight = event.dict['h']
                scaledWidth = event.dict['w'] """

            # If the user picks a coordinate, then we close the window and return the coordinates of the click
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Get outputs of Mouseclick event handler
                (mouseX, mouseY) = pygame.mouse.get_pos()

                # Update userLocation. Since we have successfully captured the user input, there are no more errors.
                userLocation = (mouseX, mouseY)

                # Paste pin on mouse position
                screen.blit(pin, (userLocation[0] - 25, userLocation[1] - 42))
                pygame.display.update()
                time.sleep(0.2)
                exit = True
                
        # While window is open, constantly refresh the window display
        pygame.display.update()

    pygame.display.quit()
    pygame.quit()
    return userLocation


# Keyword-based Search Function
# This function attempts to match the search term with the keywords of various stalls
def search_by_keyword(keyword):
    # Since keyword is non-case sensitive, we standardize it to small letters
    searchTerm = keyword.lower()

    # Load list of stalls and their keywords (dictionary within dictionary)
    stallList = load_stall_keywords()

    # Create an empty dictionary to store results found
    results = {}
    numberOfStallsFound = 0

    # Search all the stall keywords within the canteens to find matches KEY : VALUE = CANTEEN NAME : DICTIONARY OF STALLS
    # In other words, canteen = Canteen name, stalls = Dictionary of stalls
    print("Searching...")
    for canteen, stalls in stallList.items():
        # List of stalls found in this canteen
        stallsFound = []

        # KEY : VALUE = STALL NAME : KEYWORDS OF STALL (As a string)
        # i.e. stall = Stall name, keywords = Keywords of stall as a string e.g. "Halal, Chinese"
        for stall, keywords in stalls.items(): 
            # If our search term matches a keyword of a stall, we add the stall to results
            if (searchTerm in keywords.lower()) or (keywords.lower() in searchTerm):
                numberOfStallsFound += 1
                # Add that stall found and its keywords as a concantated string to a list of found stalls within this canteen
                stallsFound.append(stall + " (" + keywords + ")")
        # Add the stalls we found in this canteen to a results dictionary contained all the canteens with stalls found by the search term
        if (len(stallsFound) > 0):
            results[canteen] = stallsFound

    # Display results
    if (numberOfStallsFound <= 0):
        # If no food stalls found, we suggest keywords closest to the keyword of the user to get a match
        suggestion = suggest_keyword(searchTerm)
        if (suggestion != None):
            # If the user agrees with the suggestion, we search again with the new valid keyword
            validated = False
            while not validated:
                errorCheck = input("No food stall(s) found with input keyword '{}'. Did you mean '{}' instead? (y/n): ".format(searchTerm, suggestion.lower()))
                if (errorCheck == "y" or errorCheck == "Y"):
                    # Call function to search with the suggested keyword
                    validated = True
                    search_by_keyword(suggestion)
                elif (errorCheck == "n" or errorCheck == "N"):
                    validated = True
                    print("Exiting search by keyword...")
                # We do not understand the user input. Ask user again to confirm his/her choice.
                else:
                    print("Please input 'y' to search with the suggested keyword, or 'n' to exit to the menu.")
        else:
            print("No food stalls(s) found with input keyword '{}'. No keyword suggestions match your search term. Exiting to menu...".format(searchTerm))
       
        
    else:
        print("{} food stall(s) found matching keyword '{}':".format(numberOfStallsFound, searchTerm))

        # Sort the dictionary's keys to print canteen names in sorted order
        sortedCanteens = natural_sort(results.keys())

        # Using the sorted keys, we then access the results dictionary to print out our results in order.
        for canteenName in sortedCanteens:
            # Iterate through the list of stalls found within this particular canteen that matches the search term
            for stallFound in results[canteenName]: 
                print(canteenName + " - " + stallFound)

# Price-based Search Function
# Returns a listing of stalls that fit within a given price range
def search_by_price(minPrice, maxPrice):
    # Load list of stalls and their keywords (dictionary within dictionary)
    priceList = load_stall_prices()

    # Create an empty dictionary to store results found
    results = {}
    numberOfStallsFound = 0

    # Search all the canteens to find stalls within the price range KEY : VALUE = CANTEEN NAME : DICTIONARY OF STALLS
    # In other words, canteen = Canteen name, stalls = Dictionary of stalls
    print("Searching...")
    for canteen, stalls in priceList.items():
        # List of stalls found in this canteen
        stallsFound = {}

        # KEY : VALUE = STALL NAME : KEYWORDS OF STALL (As a string)
        # i.e. stall = Stall name, keywords = Keywords of stall as a string e.g. "Halal, Chinese"
        for stall, price in stalls.items():
            # If price range is within the search range, we add it to the results
            if (price >= minPrice and price <= maxPrice):
                numberOfStallsFound += 1
                stallsFound[stall] = price
        
        # Store into results under canteen name
        if (len(stallsFound) > 0):
            results[canteen] = stallsFound

    # Display results
    if (numberOfStallsFound <= 0):
        print("No food stall(s) found within specified price range.")
    else:
        print("{} food stall(s) found within specified price range (S${:.2f} - S${:.2f}):".format(numberOfStallsFound, minPrice, maxPrice))

        # Sort the dictionary's keys to print canteen names in sorted order
        sortedCanteens = natural_sort(results.keys())

        # Using the sorted keys, we then access the results dictionary to print out our results in order.
        for canteenName in sortedCanteens:
            # Iterate through the dictionary of stalls found within this particular canteen that matches the price range
            for stall, price in results[canteenName].items(): 
                print("{} ({}) - S${:.2f}".format(stall, canteenName, price))

# Location-based Search Function
def search_nearest_canteens(userLocation, numOfCanteens):
    # Load a list of all the canteen locations KEY: Canteen name VALUE: List[0] = Canteen x location, List[1] = Canteen y location
    locationList = load_canteen_location()
    
    # Create a dictionary to store distance of the canteen from the user
    results = {}

    # Iterate through and calculate distance of each canteen from the user
    print("Searching...")
    for canteen, coordinates in locationList.items():
        # Pythagoras theorem, x values are index 0, y values are index 1
        distanceFromUser = ((userLocation[0] - coordinates[0])**2 + (userLocation[1] - coordinates[1])**2)**(1/2)
        results[canteen] = distanceFromUser
    
    # Sort the results based on distance
    # We call the sorted function on the list of tuples (canteen, distance), and set the sorting key to be the second item in the tuple
    # sortedResults is a sorted list of tuples (canteen, distance) sorted by distance from the user
    sortedResults = sorted(results.items(), key = lambda distance: distance[1])

    # Display results
    print("{} nearest canteen(s) found:".format(numOfCanteens))
    for i in range(numOfCanteens):
        print("{} - {}m".format(sortedResults[i][0], int(sortedResults[i][1])))
    
    # We let the user choose if he/she wants to view results on a map or not
    validated = False
    while not validated:
        errorCheck = input("View results on the map? (y/n): ")
        if (errorCheck == "y" or errorCheck == "Y"):
            # Call function to display nearest canteens on the map
            validated = True
            show_nearest_canteens(userLocation, sortedResults[0:numOfCanteens])
        elif (errorCheck == "n" or errorCheck == "N"):
            validated = True
            print("Alright. Hope you enjoy the food in NTU!")
        # We do not understand the user input. Ask user again to confirm his/her choice.
        else:
            print("Please input 'y' to view the {} nearest canteens around you on the map, or 'n' to exit to the menu.".format(numOfCanteens))
    return()

# ===== Any additional function to assist search criteria ===== #

# Validates the validity of a given keyword (one word, string etc.) and returns True if valid, False if not
# This function assumes that stall names can have weird things like symbols and numbers
def validate_keyword(keyword):
    try:
        # If more than one word, raise a value error
        if (len(keyword.split()) != 1 or len(keyword) < 2):
            raise ValueError
        # Otherwise, we validate the input to be true
        else:
            return(True)
    # Error handling statements, we return false for this function to be used in other functions
    except TypeError:
        print("Kindly ensure that the keyword is a string. Please try again.")
        return(False)
    except ValueError:
        print("Only a single keyword search term is allowed, and the keyword must be at least two letters. Please try again.")
        return(False)
    except:
        print("An unexpected error has occured. Please contact the engineer for help.")
        return(False)

# Loads the list of keywords from the data list and removes duplicates
def load_suggestions():
    keywordsList = load_stall_keywords()
    noDuplicatedKeywordsList = []
    for stall in keywordsList.values():
        for keywords in stall.values():
            # Get a list of the keywords of each stall, remove spaces from each word and split by commas
            keywords = keywords.split(",")
            for keyword in keywords:
                if keyword[0] == " ":
                    keyword = keyword[1:]
                if keyword not in noDuplicatedKeywordsList:
                    noDuplicatedKeywordsList.append(keyword)
    return(noDuplicatedKeywordsList)

# This function takes in a search term (keyword) and matches it against valid and searchable keywords to find a similarity.
# It then returns the most similar term as a suggestion.
def suggest_keyword(searchTerm):
    validKeywords = load_suggestions()
    suggestion = difflib.get_close_matches(searchTerm, validKeywords, n = 1, cutoff = 0.5)
    if len(suggestion) >= 1:
        return(suggestion[0])
    else:
        return(None)

# This function validates if the prices input are correct and returns the corrected price input if any. Else, return false.
def validate_price(minPrice, maxPrice):
    try:
        validated = False
        minPrice, maxPrice = float(minPrice), float(maxPrice)

        # First check if both prices are positive numbers.
        # We allow for 0 as a value because why not search for free food?
        if (minPrice < 0 or maxPrice < 0):
            print("The search ranges for meal pricing cannot have a negative number. Please try again.")
        # Both numbers are positive, we continue checking
        else:
            # No range of prices, we check if the user only wants food at a specific price
            if (minPrice == maxPrice):
                while not (valdiated):
                    errorCheck = input("The minimum price you have input is equal to your maximum price. Search for food at this specific price only? (y/n): ")
                    # We return true for validation, confirming that the user wants to search for food at a specific price only
                    if (errorCheck == "y" or errorCheck == "Y"):
                        validated = True
                    # We jump out of the loop and return false for price validation
                    elif (errorCheck == "n" or errorCheck == "N"):
                        print("Kindly try again with the corrected price range.")
                        break
                    # We do not understand the user input. Ask user again to confirm his/her choice.
                    else:
                        print("Please input 'y' to find food at this specific price, or 'n' to input a new price range.")

            # If maxPrice is lower than minPrice, we ask the user if they want us to help them fix it (i.e. swap the price range for them)
            elif (maxPrice < minPrice):
                while not (validated):
                    errorCheck = input("The minimum price you have input is higher than your maximum price. Search for food with the price ranges swapped? (y/n): ")
                    if (errorCheck == "y" or errorCheck == "Y"):
                        minPrice, maxPrice = maxPrice, minPrice
                        validated = True
                    elif (errorCheck == "n" or errorCheck == "N"):
                        print("Minimum price should not be higher than the maximum price. Please try again.")
                        return(False)
                    # We do not understand the user input. Ask user again to confirm his/her choice.
                    else:
                        print("Please input 'y' to search for food at the corrected price range, or 'n' to input a new price range.")
            # Else price is correct, we return true
            else:
                validated = True
        # Return validated input (if valid) else return false
        if not validated:
            return(False)
        else:
            return(minPrice, maxPrice)
    
    # Error handling
    except ValueError:
        print("Please ensure that the minimum price and maximum price are positive numerical values.")
        return(False)
    except TypeError:
        print("Please ensure that the minimum price and maximum price are positive numerical values.")
        return(False)
    except:
        print("An unexpected error has occured. Please contact the engineer for help.")
        return(False)

# This function validates if the input number of canteens to find is valid. Returns the corrected input if any, else it returns False
def validate_nearest_number(numOfCanteens):
    try:
        # If not a singular integer, raise a value error
        numOfCanteens = int(numOfCanteens)
        maxNumOfCanteens = 15 # Maximum number of canteens in NTU. If input is above this number, we default to it.
        if (numOfCanteens == 0):
            raise ValueError    
        # If input is -ve, we default to 1. Else we just return the value.
        elif (numOfCanteens < 0):
            print("Negative integer detected. Defaulting search field to nearest canteen (1).")
            return(1)
        # More than the number of canteens in NTU
        elif (numOfCanteens > maxNumOfCanteens):
            print("Woops. That's more than the number of canteens in NTU! Showing you ALL our canteens instead!")
            return(15)
        else:
            return(numOfCanteens)
    # Error handling statements, we return false for this function to be used in other functions
    except TypeError:
        print("Number of restaurants must be a positive, non-zero integer.")
        return(False)
    except ValueError:
        print("Number of restaurants must be a positive, non-zero integer.")
        return(False)
    except:
        print("An unexpected error has occured. Please contact the engineer for help.")
        return(False)

# Displays the nearest canteens around the user using pygame
def show_nearest_canteens(userLocation, results):
    # Initialize pygame
    pygame.init()
    pygame.font.init()

    # Get dimensions and files
    imageLocation = "NTUcampus.jpg"
    pinLocation = "pin.png"
    foodPinLocation = "food_pin.png"
    screenTitle = "Location Based Search (NTU)"
    mapSize = (620, 750)
    pinSize = (50, 50)

    # Text variables
    font = pygame.font.SysFont("Arial", 10)
    white = (255, 255, 255) 
    black = (0, 0, 0)

    # Set screen width and height for display surface
    screen = pygame.display.set_mode(mapSize)

    # Set title of screen
    pygame.display.set_caption(screenTitle)

    # Open image file and pin file, and scale them to the desired size
    ntuMapOriginal = pygame.image.load(imageLocation).convert()
    ntuMap = pygame.transform.smoothscale(ntuMapOriginal, mapSize)
    pinOriginal = pygame.image.load(pinLocation).convert_alpha()
    pin = pygame.transform.smoothscale(pinOriginal, pinSize)
    foodPinOriginal = pygame.image.load(foodPinLocation).convert_alpha()
    foodPin = pygame.transform.smoothscale(foodPinOriginal, pinSize)

    # Load the stall location data to show on the map
    locationList = load_canteen_location()

    # Loop for the whole interface while it remains active
    exit = False
    while not exit:
        # First, we make a call to the event queue to check for events every frame
        for event in pygame.event.get():
            # User exits the window, we return an error as location was not selected
            if event.type == pygame.QUIT:
                exit = True

            # DISPLAY ELEMENTS (Map background, user location pin, nearest canteens pins)
            screen.blit(ntuMap, (0,0))
            screen.blit(pin, (userLocation[0] - 25, userLocation[1] - 42))

            # Display canteen pins first, then overlay text on top
            for canteen in results:
                canteenName = canteen[0]
                xLocation = locationList[canteenName][0]
                yLocation = locationList[canteenName][1]

                # Put canteen pin onto the display screen
                screen.blit(foodPin, (xLocation - 25, yLocation - 50))

            # Text display
            for canteen in results:
                canteenName = canteen[0]
                distance = canteen[1]
                xLocation = locationList[canteenName][0]
                yLocation = locationList[canteenName][1]

                # Add text for canteen name
                canteenText = font.render(" {} ({}m)".format(canteenName, int(distance)), True, white, black)
                textWidth = pygame.Surface.get_width(canteenText)
                screen.blit(canteenText, ((xLocation - textWidth // 2), yLocation - 20))
                
        # While window is open, constantly refresh the window display
        pygame.display.update()

    pygame.display.quit()
    pygame.quit()

# This function sorts a list of strings/numbers no matter if a number is in a string or not
# E.g. elm0, elm11, elm2, elm55 => elm0, elm2, elm11, elm55
def natural_sort(unsortedList):
    # Lambda transforms all given inputs based on the instructions given and returns it as a result
    # convert transforms any given inputs into an integer if the input is a digit. If not, it transforms the string into lowercase.
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    # alphanumKey splits given inputs into strings and numbers (e.g. "a23b" => ["a", "23", "b'"])
    # It then converts each item in the list using the convert lambda above
    alphanumKey = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    # We then sort any given list input using alphanumKey as the key for sorting
    # Since alphanumKey is a list of letters and numbers, the sorted functions is able to compare integer > interger and string > string
    # Therefore, it can sort numbers within strings and return a naturally sorted result. 
    return sorted(unsortedList, key = alphanumKey)

# Main Python Program Template

# Main Program Function
def main():
    loop = True

    while loop:
        try:    
            print("=======================")
            print("F&B Recommendation Menu")
            print("1 -- Display Data")
            print("2 -- Keyword-based Search")
            print("3 -- Price-based Search")
            print("4 -- Location-based Search")
            print("5 -- Exit Program")
            print("=======================")
            option = int(input("Please enter option [1-5]: "))

            if option == 1:
                # Print provided dictionary data structures
                print("Display Data")
                print()
                
                # Load data
                canteen_stall_keywords = load_stall_keywords("canteens.xlsx")
                canteen_stall_prices = load_stall_prices("canteens.xlsx")
                canteen_locations = load_canteen_location("canteens.xlsx")

                # Sort canteens by name
                sortedCanteens = natural_sort(canteen_stall_keywords.keys())

                # Display results
                print("Keyword Data")
                print("------------")
                for canteen in sortedCanteens:
                    print(canteen + ":")
                    for stall, keywords in canteen_stall_keywords[canteen].items():
                        print("{} ({})".format(stall, keywords))
                    print()

                print("Price Data")
                print("----------")
                for canteen in sortedCanteens:
                    print(canteen + ":")
                    for stall, price in canteen_stall_prices[canteen].items():
                        print("{} - S${:.2f}".format(stall, price))
                    print()

                print("Location Data")
                print("-------------")
                for canteen in sortedCanteens:
                    location = canteen_locations[canteen]
                    print("{} - X: {}, Y: {}".format(canteen, location[0], location[1]))

            elif option == 2:
                # keyword-based search
                print("Keyword-based Search")
                searchTerm = ""
                validated = False
                # Attempt to validate keyword (one word string only, symbols are allowed) While not validated, keep asking for new keyword
                while not (validated):
                    searchTerm = input("Enter type of food: ")
                    validated = validate_keyword(searchTerm)
                search_by_keyword(searchTerm)
    
            elif option == 3:
                # price-based search
                print("Price-based Search")
                minPrice = 0
                maxPrice = 0
                validatedPrice = False
                # Attempt to validate keyword (one word string only, symbols are allowed) While not validated, keep asking for new keyword
                while (validatedPrice == False):
                    minPrice = input("Enter minimum price: ")
                    maxPrice = input("Enter maximum price: ")
                    validatedPrice = validate_price(minPrice, maxPrice)
                
                search_by_price(validatedPrice[0], validatedPrice[1])
                
            elif option == 4:
                # Location-based search
                print("Location-based Search")
                print("Please select your current location on the map.")

                # Call PyGame function to get user's location
                userLocation = get_user_location_interface()

                # If it returns None, it means the user did not select a location, we abort as a error.
                if userLocation is None:
                    print("You did not select your current location. Aborting location based search...")
                    continue
                else:
                    print("Your location is entered at (x,y): {}, {}".format(int(userLocation[0]), int(userLocation[1])))
                
                # Validate input for k-nearest number of canteens to the user
                validatedNum = False
                while (validatedNum == False):
                    numOfCanteens = input("Please enter the number of canteens to search for around you: ")
                    validatedNum = validate_nearest_number(numOfCanteens)

                # call location-based search function
                search_nearest_canteens(userLocation, validatedNum)

            elif option == 5:
                # exit the program
                print("Exiting F&B Recommendation")
                loop = False

            else:
                raise ValueError
        except ValueError:
            print("Please input a number from 1-5 only. Please try again.")
        except TypeError:
            print("Only numbers from 1-5 are allowed for menu selection. Please try again.")
        except:
            print("An unidentified error occured. Please contact the engineers for help.")

# Run main program            
main()