import json
from web3 import Web3
from solcx import compile_standard, install_solc
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from datetime import date
from eth_abi import decode
from eth_account import Account
import re



install_solc("0.8.0")
print("installed")

with open("./Contracts/Supply_Chain.sol", "r") as file:
    solidity_file = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Supply_Chain.sol": {"content": solidity_file}},
        "settings": {
            "optimizer": {
                "enabled": True,
                "runs": 200
            },
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode"]}
            }
        }
    },
    solc_version="0.8.0"
)


with open("compiled_code2.json", "w") as file:
	json.dump(compiled_sol, file)


contract_data = {
    "User": {
        "abi": compiled_sol["contracts"]["Supply_Chain.sol"]["User"]["abi"],
        "bytecode": compiled_sol["contracts"]["Supply_Chain.sol"]["User"]["evm"]["bytecode"]["object"]
        
    },
    "Product": {
        "abi": compiled_sol["contracts"]["Supply_Chain.sol"]["ProductFuncs"]["abi"],
        "bytecode": compiled_sol["contracts"]["Supply_Chain.sol"]["ProductFuncs"]["evm"]["bytecode"]["object"]
    },
    "Supply": {
        "abi": compiled_sol["contracts"]["Supply_Chain.sol"]["Supplychain"]["abi"],
        "bytecode": compiled_sol["contracts"]["Supply_Chain.sol"]["Supplychain"]["evm"]["bytecode"]["object"]
    }
}



chain_id = 1337
##private_key=""
load_dotenv(Path('.')/'key.env') 
private_key = os.getenv("PRIVATE_KEY")

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

if not private_key:
    raise ValueError("PRIVATE_KEY not found in .env file!")

account = web3.eth.account.from_key(private_key) 
address = account.address



def deploy_contract(web3, abi, bytecode, private_key, deployer_address, constructor_args=None):
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    
    tx = contract.constructor(*constructor_args if constructor_args else []).build_transaction({
        'chainId': 1337,
        'gas': 10000000,
        'gasPrice': web3.eth.gas_price,
        'from': address,
        'nonce': web3.eth.get_transaction_count(address)
    })
    
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.contractAddress



print("Deploying Product contract...")
product_address = deploy_contract(
    web3,
    contract_data["Product"]["abi"],
    contract_data["Product"]["bytecode"],
    private_key,
    address
)
print(f"Product deployed at: {product_address}")

print("Deploying User contract...")
user_address = deploy_contract(
    web3,
    contract_data["User"]["abi"],
    contract_data["User"]["bytecode"],
    private_key,
    address
)
print(f"User deployed at: {user_address}")

print("Deploying Supply Chain contract...")
supply_address = deploy_contract(
    web3,
    contract_data["Supply"]["abi"],
    contract_data["Supply"]["bytecode"],
    private_key,
    address,
    constructor_args=[user_address, product_address]
)
print(f"Supply Chain contract deployed at: {supply_address}")
print(f"Contract code at address: {len(web3.eth.get_code(supply_address).hex())} bytes")


with open("deployed_addresses.json", "w") as f:
    json.dump({
        "User": user_address,
        "Product": product_address,
        "Supply": supply_address
    }, f, indent=2)


adduser_contract = web3.eth.contract(address=supply_address, abi=contract_data["Supply"]["abi"]) 
addaproduct_contract = web3.eth.contract(address=supply_address, abi=contract_data["Supply"]["abi"])
all_contract = web3.eth.contract(address=supply_address, abi=contract_data["Supply"]["abi"])
user_contract = web3.eth.contract(address=user_address, abi=contract_data["User"]["abi"])
prod_contract = web3.eth.contract(address=product_address, abi=contract_data["Product"]["abi"])

def add_user(user_tuple):##UserRole,userId,name,physAdres,phoneNumber,email):

    user_address = account.address
    tx = adduser_contract.functions.addauser(user_tuple).build_transaction({
        'chainId': 1337,
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'from': user_address,
        'nonce': web3.eth.get_transaction_count(user_address)
    })
    

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt

def add_product(product_tuple):##name,manufacturerName,addr_manufacturer,madeDate,quantity,barcode,price,description):

    user_address = account.address
    tx = addaproduct_contract.functions.addaproduct(product_tuple).build_transaction({
        'chainId': 1337,
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'from': user_address,
        'nonce': web3.eth.get_transaction_count(user_address)
    })
    

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt



def get_all_products():
    try:
        contract_address = supply_address
        get_all_products_contract = web3.eth.contract(address=contract_address, abi=contract_data["Supply"]["abi"])
        products = get_all_products_contract.functions.printAllProducts().call()

        
        print("\nAll Products:")
        print("-" * 40)
        
        for i, product in enumerate(products, 1):
            # Convert timestamp to readable date
            ##mDate = datetime.fromtimestamp(product[3]).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  product #{i}:")
            print(f"  name:  {product[0]}")
            print(f"  manufacturerName:  {product[1]}")
            print(f"  addr_manufacturer:  {product[2]}")
            print(f"  madeDate:  {product[3]}")
            print(f"  quantity:  {product[4]}")
            print(f"  barcode:  {product[5]}")
            print(f"  price:  {product[6]}")
            print(f"  description:  {product[7]}")
            print("-" * 40)
                        
        return products
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []

def sell_product(addr1, str1, addr2, quantity):
    
    user_address = account.address
    tx = all_contract.functions.sellaProduct(
            web3.to_checksum_address(addr1),
            str1,
            web3.to_checksum_address(addr2),
            int(quantity)).build_transaction({
        'chainId': 1337,
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'from': user_address,
        'nonce': web3.eth.get_transaction_count(user_address)
    })
    

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt:
        print("Item dispatched")
    return tx_receipt
   

def get_product_count():
    try:
        main_contract = web3.eth.contract(address=supply_address, abi=contract_data["Supply"]["abi"])
        count = main_contract.functions.getProductCount().call()
        return int(count)
    except Exception as e:
        print(f"Error getting product count: {e}")
        return None


def get_receipt_count():
    try:
        main_contract = web3.eth.contract(address=supply_address, abi=contract_data["Supply"]["abi"])
        count = main_contract.functions.getAReceiptCount().call()
        return int(count)
    except Exception as e:
        print(f"Error getting receipt count: {e}")
        return None


def get_product_keys():

    try:

        prod_count = prod_contract.functions.getProductCount().call()  
        return [prod_contract.functions.allProducts2(i).call() for i in range(prod_count)]
    except Exception as e:
        print(f"Error fetching keys: {e}")
        return []


def get_products():
    try:

        product_count = prod_contract.functions.getProductCount().call()
        prod_keys = [prod_contract.functions.allProducts2(i).call() for i in range(product_count)]
        

        products = []
        for key in prod_keys:
            name,manufacturerName,manufacturer,madeDate,quantity,barcode,price,description = prod_contract.functions.getProduct(key).call()
            products.append({
                #'key': key.hex(),
                'name': name,
                'manufacturerName': manufacturerName,
                'manufacturer': manufacturer,
                'madeDate': datetime.fromtimestamp(madeDate),
                'quantity': quantity,
                'barcode': barcode,
                'price': price,
                'description': description
            })
        return products
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_distributor_products():
    try:

        product_count = prod_contract.functions.getDistributorProducCount().call()
        prod_keys = [prod_contract.functions.Dkeys(i).call() for i in range(product_count)]

        products = []
        for key in prod_keys:
            name,manufacturerName,manufacturer,madeDate,quantity,barcode,price,description = all_contract.functions.getDistributorProductByKey(key).call()
            products.append({
                #'key': key.hex(),
                'name': name,
                'manufacturerName': manufacturerName,
                'manufacturer': manufacturer,
                'madeDate': datetime.fromtimestamp(madeDate),
                'quantity': quantity,
                'barcode': barcode,
                'price': price,
                'description': description
            })
        return products
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_retailer_products():
    try:

        product_count = prod_contract.functions.getRetailerProducCount().call()
        prod_keys = [prod_contract.functions.Rkeys(i).call() for i in range(product_count)]
        

        products = []
        for key in prod_keys:
            name,manufacturerName,manufacturer,madeDate,quantity,barcode,price,description = all_contract.functions.getRetailerProductByKey(key).call()
            products.append({
                #'key': key.hex(),
                'name': name,
                'manufacturerName': manufacturerName,
                'manufacturer': manufacturer,
                'madeDate': datetime.fromtimestamp(madeDate),
                'quantity': quantity,
                'barcode': barcode,
                'price': price,
                'description': description
            })
        return products
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_singular_product(barcode):
    try:
        barcode=str(barcode)
        count=get_product_count()

        for i in range(count):
            key = prod_contract.functions.allProducts2(i).call()
            name,manufacturerName,manufacturer,madeDate,quantity,barcode2,price,description = prod_contract.functions.getProduct(key).call()
            if barcode2.lower() == barcode.lower():
                return {
                    'name': name,
                    'manufacturerName': manufacturerName,
                    'manufacturer': manufacturer,
                    'madeDate': datetime.fromtimestamp(madeDate),
                    #'madeDate': datetime.fromtimestamp(madeDate).strftime('%d/%m/%Y'),
                    'quantity': quantity,
                    'barcode': barcode,
                    'price': price,
                    'description': description                    
                }
        return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_singular_distributor_product(barcode):
    try:
        barcode=str(barcode)
        count = prod_contract.functions.getDistributorProducCount().call()

        for i in range(count):
            key = prod_contract.functions.Dkeys(i).call()
            name,manufacturerName,manufacturer,madeDate,quantity,barcode2,price,description = all_contract.functions.getDistributorProductByKey(key).call()
            if barcode2.lower() == barcode.lower():
                return {
                    'name': name,
                    'manufacturerName': manufacturerName,
                    'manufacturer': manufacturer,
                    'madeDate': datetime.fromtimestamp(madeDate),
                    #'madeDate': datetime.fromtimestamp(madeDate).strftime('%d/%m/%Y'),
                    'quantity': quantity,
                    'barcode': barcode,
                    'price': price,
                    'description': description                    
                }
        return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_singular_retailer_product(barcode):
    try:
        barcode=str(barcode)
        count = prod_contract.functions.getRetailerProducCount().call()

        for i in range(count):
            key = prod_contract.functions.Rkeys(i).call()
            name,manufacturerName,manufacturer,madeDate,quantity,barcode2,price,description = all_contract.functions.getRetailerProductByKey(key).call()
            if barcode2.lower() == barcode.lower():
                return {
                    'name': name,
                    'manufacturerName': manufacturerName,
                    'manufacturer': manufacturer,
                    'madeDate': datetime.fromtimestamp(madeDate),
                    #'madeDate': datetime.fromtimestamp(madeDate).strftime('%d/%m/%Y'),
                    'quantity': quantity,
                    'barcode': barcode,
                    'price': price,
                    'description': description                    
                }
        return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None


def print_user(addr1):


    raw_user = all_contract.functions.findaUser(addr1).call()

    if isinstance(raw_user, bytes):
        decoded = decode(['uint8','address','string','string','string','string'], raw_user)
    else:
        decoded = raw_user

##    decoded = decode_abi(['uint8','address','string','string','string','string'], bytes.fromhex(raw_user.hex()[2:]))
               
    role, userId_, name, physAdress, phoneNumber, email = decoded

    if userId_=="0x0000000000000000000000000000000000000000":
        print("User doesn't exists.")
    else:
        if role==0:
            us_role = "Manufacturer"
        elif role==1:
            us_role = "Supplier"
        elif role==2:
            us_role = "Distributor"
        elif role==3:
            us_role = "Retailer"
        elif role==4:
            us_role = "Customer"
        print("-" * 40)
        print(f"User Info for {addr1}:")
        print(f"role: {us_role}")
        print(f"Wallet: {userId_}")
        print(f"Name: {name}")
        print(f"Home address: {physAdress}")
        print(f"Phone Number: {phoneNumber}:")
        print(f"e-mail: {email}")
        print("-" * 40)
        return role, userId_, name, physAdress, phoneNumber, email

def desired_role(addr1):

    raw_user = all_contract.functions.findaUser(addr1).call()

    if isinstance(raw_user, bytes):
        decoded = decode(['uint8','address','string','string','string','string'], raw_user)
    else:
        decoded = raw_user
               
    role, userId_, name, physAdress, phoneNumber, email = decoded

    if userId_=="0x0000000000000000000000000000000000000000":
        print("User doesn't exists.")
    else:
        if role==0:
            return 0
        elif role==1:
            return 1
        elif role==2:
            return 2
        elif role==3:
            return 3
        elif role==4:
            return 4


def find_user(addr1):

    raw_user = all_contract.functions.findaUser(addr1).call()

    if isinstance(raw_user, bytes):
        decoded = decode(['uint8','address','string','string','string','string'], raw_user)
    else:
        decoded = raw_user
               
    role, userId_, name, physAdress, phoneNumber, email = decoded

    return role, userId_, name, physAdress, phoneNumber, email

def check_user_exists(addr1):

    try:
        raw_user = all_contract.functions.findaUser(addr1).call()
        if isinstance(raw_user, bytes):
            decoded = decode(['uint8','address','string','string','string','string'], raw_user)
        else:
            decoded = raw_user
        role, userId_, name, physAdress, phoneNumber, email = decoded
##        print(f"Wallet: {userId_}")
##        print(f"Name: {name}")
        if name == "" and userId_ == "0x0000000000000000000000000000000000000000":
            return 1
        else:
            return 0 
        
    except Exception as e:
        return 1


def check_user_role(addr1):

    try:

        raw_user = all_contract.functions.findaUser(addr1).call()
        if isinstance(raw_user, bytes):
            decoded = decode(['uint8','address','string','string','string','string'], raw_user)
        else:
            decoded = raw_user
        role, userId_, name, physAdress, phoneNumber, email = decoded

        if role == 0:
            return 0
        elif role == 1:
            return 1
        elif role == 2:
            return 2
        elif role == 3:
            return 3
        elif role == 4:
            return 4
        else:
            return 5
        
    except Exception as e:
        return 5

def get_address():
    while True:
        addr_input = input("Enter address: ").strip()
        
        if Web3.is_address(addr_input):
            checksum_addr = Web3.to_checksum_address(addr_input)
            print(f"Valid address (checksum): {checksum_addr}")
            return checksum_addr
        else:
            print("Invalid address. Try again.")

def valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def make_user(addr,rol):

    name  = input("Enter user name: ")

    if rol ==0:
        print("User's role is a manufacturer")
        num2=0
    else:
        print("\nPress 0 if the new user is manufacturer. ")
        print("\nPress 1 if the new user is Supplier. ")
        print("\nPress 2 if the new user is Distributor. ")
        print("\nPress 3 if the new user is Retailer. ")
        print("\nPress 4 if the new user is Customer. ")

        while True:
            try:
                num2  = int(input("Enter a number 0 through 4: "))
                if num2>4 or num2<0:
                    print("\nWrong input number")
                else:
                    break
            except ValueError:      
                print("\nSorry, that is not an integer. Please try again.")

    home_address  = input("Enter user's home address: ")
    while True:
        try:
            phone_number  = int(input("Enter user's phone number. "))
            if 6900000000 <= phone_number <7000000000:
                phone_number=str(phone_number)
                break
            else:
                print("You didn't enter a valid phone number.")
        except ValueError:      
            print("\nYou didn't enter a valid phone number.")


                
    while True:
        email = input("Enter user's email: ")
        if valid_email(email):
            break
        else:
            print("Invalid email!")

    user_tuple = (num2,addr,name,home_address,phone_number,email)
    receipt2 = add_user(user_tuple)
    if receipt2:
        print("User added")
    else:
        print("Failed to add user")


def make_buyer(addr,rol,addr2):

    name  = input("Enter user name: ")

    if rol ==0:
        print("User's role is a manufacturer")

    elif rol ==1:
        print("User's role is a Supplier")

    elif rol ==2:
        print("User's role is a Distributor")

    elif rol ==3:
        print("User's role is a Retailer")

    else:
        print("User's role is a Customer. ")
        rol=4


    home_address  = input("Enter user's home address: ")
    while True:
        try:
            phone_number  = int(input("Enter user's phone number. "))
            if 6900000000 <= phone_number <7000000000:
                phone_number=str(phone_number)
                break
            else:
                print("You didn't enter a valid phone number.")
        except ValueError:      
            print("\nYou didn't enter a valid phone number.")


                
    while True:
        email = input("Enter user's email: ")
        if valid_email(email):
            break
        else:
            print("Invalid email!")

    user_tuple = (rol,addr,name,home_address,phone_number,email)

    receipt2 = add_buyer(user_tuple,addr2)
    if receipt2:
        print("User added")
    else:
        print("Failed to add user")


def add_buyer(user_tuple,addr):##UserRole,userId,name,physAdres,phoneNumber,email):

    user_address = account.address
    tx = user_contract.functions.addBuyer(user_tuple,addr).build_transaction({
        'chainId': 1337,
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'from': user_address,
        'nonce': web3.eth.get_transaction_count(user_address)
    })
    

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt

#returns 1 if product with the same name exists
def checkProductName(name):
    try:
        result = prod_contract.functions.checkProductName(name).call()
        if result==1:
            return 1
        else:
            return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 3

#returns 1 if product with the same barcode exists
def checkProductBarcode(barcode):
    try:
        result = prod_contract.functions.checkProductBarcode(barcode).call()
        if result==1:
            return 1
        else:
            return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 3

#returns 1 if distributor product with the same barcode exists
def checkDistributorProductBarcode(barcode):
    try:
        
        all_dproducts = get_distributor_products()
        for product in all_dproducts:
            if product['barcode'] == barcode:
                return 1
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 3
    


#returns 1 if product with the same barcode exists
def checkRetailerProductBarcode(barcode):
    try:
        
        all_dproducts = get_retailer_products()
        for product in all_dproducts:
            if product['barcode'] == barcode:
                return 1
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 3

#takes a date in a format we know and makes it a timestamp
def make_timestamp(date):
    dates = [
        '%d/%m/%y',
        '%d-%m-%y',
        '%d/%m/%Y', 
        '%d-%m-%Y'
    ]
    
    for fmt in dates:
        try:
            date_object = datetime.strptime(date, fmt)
            return int(date_object.timestamp())
        except ValueError:
            continue
    
    return 0

#function for a user to enter a product
def make_product(addr,manuf_name,barcode2):
        
    while True:
        name  = str(input("Give the name of the new Product: "))
        if checkProductName(name)==1:
            print("Product with the same name already exists")
        elif checkProductName(name)==0:
            break
        else:
            print("Something went wrong")    
    
    while True:
        date = input("Enter Made date of Product (DD/MM/YY or DD-MM-YY or DD/MM/YYYY or DD-MM-YYYY): ")
        made_date=make_timestamp(date)
        if made_date==0:
            print("You entered wrong date format")
        else:
            break
            
    while True:
        try:
            quantity  = int(input("Give the quantity of the Product: "))
            if quantity>9999999999 or quantity<0:
                print("\nCan't enter this quantity")
            else:
                break
        except ValueError:      
            print("\nSorry, that is not an integer. Please try again.")

    if barcode2==0:
        while True:
            try:
                barcode  = int(input("Give a barcode in range of 100000 to 999999: "))
                if barcode>999999 or barcode<100000:
                    print("\nCan't enter this barcode.")
                else:
                    barcode=str(barcode)
                    if checkProductBarcode(barcode)==1:
                        print("Product with this barcode already exists.")
                        continue
                    break
            except ValueError:      
                print("\nSorry, that is not an integer. Please try again.")
    else:
        barcode=barcode2

    while True:
        try:
            price  = int(input("Give the price of the Product: "))
            if price>99999999999 or price<0:
                print("\nCan't enter this price.")
            else:
                break
        except ValueError:      
            print("\nSorry, that is not an integer. Please try again.")

    description  = str(input("Give a small description for the Product: "))

    
    product_tuple = (name,manuf_name,addr,made_date,quantity,barcode,price,description)
    receipt3 = add_product(product_tuple)
    if receipt3:
        print("Product added.")
    else:
        print("Failed to add product.")


#function for a supplier to enter a material
def make_material(addr,supplier_name,barcode2):
        
    while True:
        name  = str(input("Give the name of the material: "))
        if checkProductName(name)==1:
            print("Material with the same name already exists")
        elif checkProductName(name)==0:
            break
        else:
            print("Something went wrong")    
    
    while True:
        date = input("Enter the date the material got created or updated (DD/MM/YY or DD-MM-YY or DD/MM/YYYY or DD-MM-YYYY): ")
        made_date=make_timestamp(date)
        if made_date==0:
            print("You entered wrong date format")
        else:
            break
            
    while True:
        try:
            quantity  = int(input("Give the quantity of the Material: "))
            if quantity>9999999999 or quantity<0:
                print("\nCan't enter this quantity")
            else:
                break
        except ValueError:      
            print("\nSorry, that is not an integer. Please try again.")

    if barcode2==0:
        while True:
            try:
                barcode  = int(input("Give a barcode in range of 100000 to 999999: "))
                if barcode>999999 or barcode<100000:
                    print("\nCan't enter this barcode.")
                else:
                    barcode=str(barcode)
                    if checkProductBarcode(barcode)==1:
                        print("Material with this barcode already exists.")
                        continue
                    break
            except ValueError:      
                print("\nSorry, that is not an integer. Please try again.")
    else:
        barcode=barcode2

    while True:
        try:
            price  = int(input("Give the price of the Product: "))
            if price>99999999999 or price<0:
                print("\nCan't enter this price.")
            else:
                break
        except ValueError:      
            print("\nSorry, that is not an integer. Please try again.")

    description  = "material"
    
    product_tuple = (name,supplier_name,addr,made_date,quantity,barcode,price,description)
    receipt3 = add_product(product_tuple)
    if receipt3:
        print("Material added.")
    else:
        print("Failed to add Material.")

def return_user_role(role):
    if role==0:
        us_role = "Manufacturer"
        return us_role
    elif role==1:
        us_role = "Supplier"
        return us_role
    elif role==2:
        us_role = "Distributor"
        return us_role
    elif role==3:
        us_role = "Retailer"
        return us_role
    elif role==4:
        us_role = "Customer"
        return us_role

def get_all_receipts():
    receipts = []
    receipts_count = get_receipt_count()
    if receipts_count==0:
        return 0
    
    for i in range(receipts_count):
        receipt = prod_contract.functions.getReceiptByIndex(i).call()
        receipts.append({          
            'receiptId': receipt[0],
            'from': receipt[1],
            'to': receipt[2],
            'productBarcode': receipt[3],
            'status': receipt[4],
            'delivered': receipt[5],
            'quantity': receipt[6],
            'num': receipt[7]
        })
    return receipts

def return_receipt_status(status):
    if status==0:
        res_status = "Manufactured"
        return res_status
    elif status==1:
        res_status = "Delivering to Supplier"
        return res_status
    elif status==2:
        res_status = "Delivering to Distributor"
        return res_status
    elif status==3:
        res_status = "Delivering to Retailer"
        return res_status
    elif status==4:
        res_status = "Delivering to Customer"
        return res_status

    
def select_receipt(barcode):
    barcode=str(barcode)
    receipts = get_all_receipts()
    match_receipts = [r for r in receipts if r['productBarcode'].lower() == barcode.lower()]

    if not match_receipts:
        print(f"No Receipt found with barcode: {barcode}")
        return None

    print(f"\nAll receipts with barcode: {barcode}")
    for i, receipt in enumerate(match_receipts, 1):
        print(f"\nReceipt #{i}:")        
        print(f"Id of receipt: {receipt['receiptId']}")
        print(f"Wallet of Seller: {receipt['from']}")
        print(f"Wallet of Buyer: {receipt['to']}")
        print(f"Barcode of the product: {receipt['productBarcode']}")
        print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
        print(f"Product quantity: {receipt['quantity']}")

    while True:
        try:
            num = int(input("\nSelect a receipt (1, 2, ...): "))
            if 1 <= num <= len(match_receipts):
                bar_receipt = match_receipts[num - 1]
                print(f"\nSelected receipt: Seller={bar_receipt['from']}, Receipt-ID={bar_receipt['receiptId']}, Product Barcode={bar_receipt['productBarcode']}")
                return bar_receipt
            else:
                print("Invalid number. Try again:")
        except ValueError:
            print("Invalid number. Try again:")


def resolve_receipt(addr1, receiptid, barcode):
    barcode=str(barcode)
    user_address = account.address
    tx = all_contract.functions.resolveAReceipt(
            web3.to_checksum_address(addr1),
            int(receiptid),
            barcode).build_transaction({
        'chainId': 1337,
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'from': user_address,
        'nonce': web3.eth.get_transaction_count(user_address)
    })
    

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if tx_receipt:
        print("Receipt resolved")
    return tx_receipt


def check_all_functions():

    
    print("Available functions in contract:")
    for func in prod_contract.functions:
        print(f"  - {func}")


def checksellbarcode():
    while  True:
        try:
            barcode  = int(input("Give the barcode of the material you want to sell (100000 to 999999): "))
            if barcode>999999 or barcode<100000:
                print("\nCan't enter this barcode.")
            else:
                barcode=str(barcode)
                if checkProductBarcode(barcode)==1:
                    mater = get_singular_product(barcode)
                    if mater['description']=="material":
                        return barcode
                    else:
                        print("This isn't a material")
                else:
                    print("Material with this barcode doesn't exist, you have to added it.")
                    barcode=str(barcode)
                    make_product(log_address,name,barcode)
                
        except ValueError:      
            print("\nSorry, that is not an integer. Please try again.")
    


#------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    account = web3.eth.account.from_key(private_key)
    
    users_to_add = [
        (0,
        Web3.to_checksum_address("0xa54d3c09E34aC96807c1CC397404bF2B98DC4eFb"),
        "Nick",
        "Athens",
        "6941234567",
        "nick@gmail.com"),
        (0,
        Web3.to_checksum_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"),
        "Dell",
        "Athens",
        "6941236824",
        "dell@gmail.com"),
        (1,
        Web3.to_checksum_address("0x5B38Da6a701c568545dCfcB03FcB875f56beddC4"),
        "Kostas",
        "Patras",
        "6941239876",
        "kostas@gmail.com"),
        (2,
        Web3.to_checksum_address("0xc0ffee254729296a45a3885639AC7E10F9d54979"),
        "Andrew",
        "Athens",
        "6941233267",
        "andrew@gmail.com"),
        (3,
        Web3.to_checksum_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"),
        "George",
        "Athens",
        "6941222267",
        "george@gmail.com"),
        (4,
        Web3.to_checksum_address("0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"),
        "pete",
        "Athens",
        "6981222267",
        "pete@gmail.com")
        
    ]
    # Add some users
    for i, user in enumerate(users_to_add, 1):
        receipt = add_user(user)
        if receipt:
            continue
        else:
            print("Failed to add user")

    products_to_add = [
        ("key xi",
        "Dell",
        Web3.to_checksum_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"),
        1690284431,
        2000,
        "123456",
        1000,
        "keyboard"),
                        
        ("key xii",
        "Dell",
        Web3.to_checksum_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"),
        1690284431,
        2000,
        "123457",
        1000,
        "keyboard"),
                        
        ("key xiii",
        "Dell",
        Web3.to_checksum_address("0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"),
        1690284431,
        2000,
        "123458",
        1000,
        "keyboard"),
                        
        ("plastic",
        "Kostas",
        Web3.to_checksum_address("0x5B38Da6a701c568545dCfcB03FcB875f56beddC4"),
        1690284431,
        2000,
        "123459",
        1000,
        "material")
    ]
    
    # Add some products
    for i, product in enumerate(products_to_add, 1):
        receipt = add_product(product)
        if receipt:
            continue
        else:
            print("Failed to add products")


    while True:
        try:
            print("You have to login to enter the application")
            log_address = get_address()

            if log_address == "0xa54d3c09E34aC96807c1CC397404bF2B98DC4eFb":
                print("You entered as admin.")
            
                while True:
                    print("-" * 40)
                    print("\n1.) Add a user. ")
                    print("\n2.) Add a product. ")
                    print("\n3.) Show all products on database. ")
                    print("\n4.) Number of products. ")
                    print("\n5.) Sell a product ")
                    print("\n6.) Number of receipts ")
                    print("\n7.) Show products with their current quantities. ")
                    print("\n8.) Find a user from address. ")
                    print("\n9.) Print all receipts. ")
                    print("\n10.) Resolve a receipt if a product reached its destination. ")
                    print("\n11.) Log out. ")
                    print("-" * 40)
                    while True:
                        try:
                            num  = int(input("Enter a number 1 through 11: "))
                            if num>11 or num<1:
                                print("\nWrong input number")
                            else:
                                break
                        except ValueError:      
                            print("\nSorry, that is not an integer. Please try again.")

                    if num==1:               
                        print("Enter the wallet address of the new user: ")
                        address = get_address()
                        if check_user_exists(address) == 0:
                            print("User already exists.")
                            continue
                        make_user(address,1)
                            
                    elif num==2:
                        print("Enter the address of the manufacturer: ")
                        address = get_address()
                        if check_user_exists(address) == 0:
                            print("User with this address exists.")
                            role, userId_, name, physAdress, phoneNumber, email=find_user(address)
                            if role == 0:
                                print("User is a manufacturer with name: %s" %name)
                                make_product(address,name,0)
                            else:
                                print("User isn't a manufacturer.")
                                continue
                        else:
                            print("You have to add the manufacturer of the product.")
                            make_user(address,0)
                            role, userId_, name, physAdress, phoneNumber, email=find_user(address)
                            make_product(address,name,0)


                            
                    elif num==3:
                        # print all products
                        all_products = get_all_products()
                        
                    elif num==4:
                        # print products count
                        count = get_product_count()
                        print(f"Current product count: {count}")
                        
                    elif num==5:
                        # sell a product
                        print("Enter the address of the seller.")
                        address = get_address()
                        if check_user_exists(address) == 0:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(address)
                            print("User with this address exists with name: %s" %name)
                        else:
                            print("You have to add the user in order to make a sale.")
                            make_user(address,1)
                            role, userId_, name, physAdress, phoneNumber, email=find_user(address)

                        print("Enter the address of the buyer.")
                        address2 = get_address()
                        if check_user_exists(address2) == 0:
                            role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)
                            print("User with this address exists with name: %s" %name2)
                        else:
                            print("You have to add the user in order to make a sale.")
                            make_user(address2,1)
                            role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)

                        counter=0
                        while True:
                            if role==0 and role2==1:
                                counter=1
                                #print("")
                                break
                            elif role==1 and role2==2:
                                counter=1
                                #print("")
                                break
                            elif role==2 and role2==3:
                                counter=1
                                #print("")
                                break
                            elif role==3 and role2==4:
                                counter=1
                                #print("")
                                break
                            else:
                                role1=return_user_role(role)
                                role2=return_user_role(role2)
                                print("User with role: %s can't sell to a user with role: %s" % (role1, role2))
                                break

                        if counter==1:
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to sell (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            break
                                        else:
                                            print("Product with this barcode doesn't exist, you have to added it.")
                                            if role==0:
                                                barcode=str(barcode)
                                                make_product(address,name,barcode)
                                            else:
                                                print("You have to add the manufacturer of the product.")
                                                while True:
                                                    address3 = get_address()
                                                    if check_user_exists(address) == 0:
                                                        role3, userId3_, name3, physAdress3, phoneNumber3, email3=find_user(address3)
                                                        if role3==0:
                                                            print("Manufacturer with this address exists with name: %s" %name3)
                                                            barcode=str(barcode)
                                                            make_product(address3,name3,barcode)
                                                            break
                                                        else:
                                                            print("This user isn't a manufacturer, so he can't add a product")
                                                    else:
                                                        print("you have to add the Manufacturer in order to make a sale")
                                                        make_user(address3,0)
                                                        role3, userId3_, name3, physAdress3, phoneNumber3, email3=find_user(address3)
                                                        print("And now to add the product")
                                                        barcode=str(barcode)
                                                        make_product(address3,name3,barcode)
                                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_product(barcode)
                            quantity2=s_product['quantity']
                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the product you want to sell: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the product you want to buy.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Selling product")
                            sell_product(address,barcode,address2,quantity)
                        
                    elif num==6:
                        rec_count = get_receipt_count()
                        print(f"Current receipt count: {rec_count}")
                    elif num==7:
                        print("All Products:")
                        for product in get_products():
                            #print(f"\nKey: {product['key']}")
                            print("-" * 40)
                            print(f"\nName: {product['name']}")
                            print(f"Manufacturer Name: {product['manufacturerName']}")
                            print(f"Wallet address of manufacturer: {product['manufacturer']}")
                            print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"Quantity: {product['quantity']}")
                            print(f"Barcode: {product['barcode']}")
                            print(f"Price: {product['price']}")
                            print(f"Description: {product['description']}")
                            print("-" * 40)
                            
                    elif num==8:
                        # find a user
                        address = get_address()
                        print(f"\n \nFinding User...")
                        print_user(address)
                        
                    elif num==9:
                        receipts_count = get_receipt_count()
                        if receipts_count==0:
                            print("\nNo Product sold yet.")
                            continue
                        print("\nAll Receipts: ")
                        print("-" * 40)
                        for i, receipt in enumerate(get_all_receipts(), 1):
                            print(f"\nReceipt #{i}:")
                            print(f"Id of receipt: {receipt['receiptId']}")
                            print(f"Wallet of Seller: {receipt['from']}")
                            print(f"Wallet of Buyer: {receipt['to']}")
                            print(f"Barcode of the product: {receipt['productBarcode']}")
                            status=return_receipt_status(receipt['status'])
                            print(f"Delivery status of product: {status}")
                            print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                            print(f"Product quantity: {receipt['quantity']}")
                            #print(f"Date: {receipt['num']}")
                            print("-" * 40)

                    elif num==10:
                        receipts_count = get_receipt_count()
                        if receipts_count==0:
                            print("\nNo Product sold yet, so no receipts available yet.")
                            continue
                        while True:
                            try:
                                barcode  = int(input("Give the barcode of the sold product (100000 to 999999): "))
                                if barcode>999999 or barcode<100000:
                                    print("\nCan't enter this barcode.")
                                else:
                                    receipts_count = get_receipt_count()
                                    if receipts_count==0:
                                        print("\nAll receipts are resolved.")
                                        continue
                                    barcode=str(barcode)
                                    if checkProductBarcode(barcode)==1:
                                        barcode=str(barcode)
                                        one_receipt = select_receipt(barcode)
                                        if one_receipt:
                                            if one_receipt['delivered']:
                                                print("Receipt is already resolved")
                                                break
                                            else:
                                                resolve_receipt(one_receipt['to'], one_receipt['receiptId'], barcode)
                                            if one_receipt:
                                                print("You selected the receipt with ID:", one_receipt['receiptId'])
                                            break
                                    else:
                                        print("Product with this barcode doesn't exist.")
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")
                    elif num==11:
                        break

            else:
                if check_user_exists(log_address) == 0:
                    role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                    print("User with this address exists with name: %s" %name)
                else:
                    print("You have to Sign up, in order to continue.")
                    make_user(log_address,1)
                    role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
        #------------------------------------------------------------------------------------------------------------------------------------
                if role==0:
                    print("User is a Manufacturer.")
                    while True:
                        print("-" * 40)
                        print("\n1.) Add a buyer. ")
                        print("\n2.) Add a product. ")
                        print("\n3.) Show all created products. ")
                        print("\n4.) Buy a material ")
                        print("\n5.) Sell a product ")
                        print("\n6.) Print all receipts. ")
                        print("\n7.) Resolve a receipt if a material reached its destination. ")
                        print("\n8.) Find a user from address. ")
                        print("\n9.) Log out. ")
                        print("-" * 40)
                        while True:
                            try:
                                num  = int(input("Enter a number 1 through 9: "))
                                if num>9 or num<1:
                                    print("\nWrong input number")
                                else:
                                    break
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")



                        if num==1:               
                            print("Enter the wallet address of the new buyer: ")
                            address = get_address()
                            if check_user_exists(address) == 0:
                                print("Buyer already exists.")
                                continue
                            make_buyer(address,2,log_address)
                                
                        elif num==2:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                            make_product(log_address,name,0)


                                
                        elif num==3:
                            print("All Created Products:")
                            for product in get_products():
                                #if product['manufacturer']==log_address:
                                if Web3.to_checksum_address(product['manufacturer']) == Web3.to_checksum_address(log_address):
                                    print("-" * 40)
                                    print(f"\nName: {product['name']}")
                                    print(f"Manufacturer Name: {product['manufacturerName']}")
                                    print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                    print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                    print(f"Quantity: {product['quantity']}")
                                    print(f"Barcode: {product['barcode']}")
                                    print(f"Price: {product['price']}")
                                    print(f"Description: {product['description']}")
                                    print("-" * 40)
                            
                        elif num==4:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)

                            counter=0
                            for product2 in get_products():
                                if product2['description'] == "material":
                                    counter=1
                            if counter==0:
                                print("There are no available material to buy.")
                                continue

                            mat  = str(input("Enter y or Y if yoy want to see all available materials: "))
                            if mat=="y" or mat=="Y":
                                print("All Materials:")
                                for product in get_products():
                                    if product['description'] == "material":
                                        print("-" * 40)
                                        print(f"\nName: {product['name']}")
                                        print(f"Manufacturer Name: {product['manufacturerName']}")
                                        print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                        print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                        print(f"Quantity: {product['quantity']}")
                                        print(f"Barcode: {product['barcode']}")
                                        print(f"Price: {product['price']}")
                                        print(f"Description: {product['description']}")
                                        print("-" * 40)

                            should_break = False
                            while True and not should_break:
                                try:
                                    barcode  = int(input("Give the barcode of the material you want to buy (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                                
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:

                                            for product3 in get_products():
                                                if product3['barcode'] == barcode:
                                                    if product3['description'] != "material":
                                                        print("you didn't enter the barcode of a material.")
                                                        continue
                                                    else:
                                                        should_break = True
                                                        break
                                        else:
                                            print("Material with this barcode doesn't exist.")

                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_product(barcode)
                            quantity2=s_product['quantity']
                            addr1 = s_product['manufacturer']
                            ##should_break = False
                            while True: ##and not should_break:
                                try:
                                    quantity  = int(input("Give the quantity of the material you want to buy: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the material you want to buy.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        ##should_break = True
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Buying  material")
                            sell_product(addr1,barcode,log_address,quantity)
                            
                            
                        elif num==5:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                            print("Enter the address of the buyer.")
                            address2 = get_address()
                            if check_user_exists(address2) == 0:
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)
                                print("User with this address exists with name: %s" %name2)
                            else:
                                print("You have to add the buyer in order to make a sale.")
                                make_buyer(address2,2,log_address)
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)

                            
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to sell (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            break
                                        else:
                                            print("Product with this barcode doesn't exist, you have to added it.")
                                            barcode=str(barcode)
                                            make_product(log_address,name,barcode)
                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_product(barcode)
                            quantity2=s_product['quantity']
                            addr1 = s_product['manufacturer']
                            if Web3.to_checksum_address(addr1) == Web3.to_checksum_address(log_address):
                                while True:
                                    try:
                                        quantity  = int(input("Give the quantity of the product you want to sell: "))
                                        if quantity>quantity2:
                                            print("Not enough quantity from the product you want to sell.")
                                            print("Maximum quantity is %d units." %quantity2)
                                        else:
                                            break
                                    except ValueError:      
                                        print("\nSorry, that is not an integer. Please try again.")
                                        
                                print(f"Selling product")
                                sell_product(log_address,barcode,address2,quantity)
                            else:
                                print("This isn't a product you can sell")


                        elif num==6:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                print(f"\nReceipt #{i}:")
                                print(f"Id of receipt: {receipt['receiptId']}")
                                print(f"Wallet of Seller: {receipt['from']}")
                                print(f"Wallet of Buyer: {receipt['to']}")
                                print(f"Barcode of the product: {receipt['productBarcode']}")
                                status=return_receipt_status(receipt['status'])
                                print(f"Delivery status of product: {status}")
                                print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                print(f"Product quantity: {receipt['quantity']}")
                                print("-" * 40)

                        elif num==7:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet, so no receipts available yet.")
                                continue
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the sold product (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        receipts_count = get_receipt_count()
                                        if receipts_count==0:
                                            print("\nAll receipts are resolved.")
                                            continue
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            barcode=str(barcode)
                       
                                            one_receipt = select_receipt(barcode)
                                            if one_receipt:
                                                if Web3.to_checksum_address(one_receipt['to']) == Web3.to_checksum_address(log_address):
                                                    if one_receipt['delivered']:
                                                        print("Receipt is already resolved")
                                                        break
                                                    else:
                                                        resolve_receipt(one_receipt['to'], one_receipt['receiptId'], barcode)
                                                    if one_receipt:
                                                        print("You selected the receipt with ID:", one_receipt['receiptId'])
                                                    break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                            
          
                                
                        elif num==8:
                            # find a user
                            address = get_address()
                            print(f"\n \nFinding User...")
                            print_user(address)

                        elif num==9:
                            break
                            


        #------------------------------------------------------------------------------------------------------------------------------------            
                elif role==1:
                    print("User is a Supplier.")
                    while True:
                        print("-" * 40)
                        print("\n1.) Add a buyer. ")
                        print("\n2.) Add a Material. ")
                        print("\n3.) Show all inserted material. ")
                        print("\n4.) Sell a material ")
                        print("\n5.) Print all receipts. ")
                        print("\n6.) Print all receipts for the materials I sold. ")
                        print("\n7.) Find a user from address. ")
                        print("\n8.) Log out. ")
                        print("-" * 40)
                        while True:
                            try:
                                num  = int(input("Enter a number 1 through 8: "))
                                if num>8 or num<1:
                                    print("\nWrong input number")
                                else:
                                    break
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")

                        if num==1:               
                            print("Enter the wallet address of the new buyer: ")
                            address = get_address()
                            if check_user_exists(address) == 0:
                                print("Buyer already exists.")
                                continue
                            make_buyer(address,0,log_address)
                                
                        elif num==2:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                            make_material(log_address,name,0)
          
                        elif num==3:
                            print("All Inserted Material:")
                            for product in get_products():
                                if Web3.to_checksum_address(product['manufacturer']) == Web3.to_checksum_address(log_address):
                                    print("-" * 40)
                                    print(f"\nName: {product['name']}")
                                    print(f"Manufacturer Name: {product['manufacturerName']}")
                                    print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                    print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                    print(f"Quantity: {product['quantity']}")
                                    print(f"Barcode: {product['barcode']}")
                                    print(f"Price: {product['price']}")
                                    print(f"Description: {product['description']}")
                                    print("-" * 40)
                                
                
                 
                        elif num==4:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                            print("Enter the address of the buyer.")
                            address2 = get_address()
                            if check_user_exists(address2) == 0:
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)
                                print("User with this address exists with name: %s" %name2)
                            else:
                                print("You have to add the buyer in order to make a sale.")
                                make_buyer(address2,2,log_address)
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)

                            barcode=checksellbarcode()

                            s_product = get_singular_product(barcode)

                            quantity2=s_product['quantity']
                            addr1 = s_product['manufacturer']
                            if Web3.to_checksum_address(addr1) == Web3.to_checksum_address(log_address):
                                while True:
                                    try:
                                        quantity  = int(input("Give the quantity of the material you want to sell: "))
                                        if quantity>quantity2:
                                            print("Not enough quantity from the material you want to sell.")
                                            print("Maximum quantity is %d units." %quantity2)
                                        else:
                                            break
                                    except ValueError:      
                                        print("\nSorry, that is not an integer. Please try again.")
                                        
                                print(f"Selling material")
                                sell_product(log_address,barcode,address2,quantity)
                            else:
                                print("This isn't a product you can sell")


                        elif num==5:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                print(f"\nReceipt #{i}:")
                                print(f"Id of receipt: {receipt['receiptId']}")
                                print(f"Wallet of Seller: {receipt['from']}")
                                print(f"Wallet of Buyer: {receipt['to']}")
                                print(f"Barcode of the product: {receipt['productBarcode']}")
                                status=return_receipt_status(receipt['status'])
                                print(f"Delivery status of product: {status}")
                                print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                print(f"Product quantity: {receipt['quantity']}")
                                print("-" * 40)

          
                        elif num==6:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['from']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40) 

                                
                        elif num==7:
                            # find a user
                            address = get_address()
                            print(f"\n \nFinding User...")
                            print_user(address)

                        elif num==8:
                            break

        #------------------------------------------------------------------------------------------------------------------------------------
                elif role==2:
                    print("User is a Distributor.")

                    while True:
                        print("-" * 40)
                        print("\n1.) Add a buyer. ")
                        print("\n2.) Show all available products. ")
                        print("\n3.) Buy a product ")
                        print("\n4.) Sell a product ")
                        print("\n5.) Print all receipts for the products you sold. ")
                        print("\n6.) Print all receipts for the products you buyed. ")
                        print("\n7.) Print all receipts. ")
                        print("\n8.) Resolve a receipt if a product reached its destination. ")
                        print("\n9.) Find a user from address. ")
                        print("\n10.) Log out. ")
                        print("-" * 40)
                        while True:
                            try:
                                num  = int(input("Enter a number 1 through 10: "))
                                if num>10 or num<1:
                                    print("\nWrong input number")
                                else:
                                    break
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")

                        if num==1:               
                            print("Enter the wallet address of the new buyer: ")
                            address = get_address()
                            if check_user_exists(address) == 0:
                                print("Buyer already exists.")
                                continue
                            make_buyer(address,3,log_address)
                                

                                
                        elif num==2:
                            print("All Available Products:")
                            for product in get_products():
                                print("-" * 40)
                                print(f"\nName: {product['name']}")
                                print(f"Manufacturer Name: {product['manufacturerName']}")
                                print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"Quantity: {product['quantity']}")
                                print(f"Barcode: {product['barcode']}")
                                print(f"Price: {product['price']}")
                                print(f"Description: {product['description']}")
                                print("-" * 40)
                            
                        elif num==3:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)

                            counter=0
                            for product2 in get_products():
                                if product2['description'] != "material":
                                    counter=1
                            if counter==0:
                                print("There are no available products to buy.")
                                continue

                            mat  = str(input("Enter y or Y if you want to see all available products: "))
                            if mat=="y" or mat=="Y":
                                print("All Products:")
                                for product in get_products():
                                    if product['description'] != "material":
                                        print("-" * 40)
                                        print(f"\nName: {product['name']}")
                                        print(f"Manufacturer Name: {product['manufacturerName']}")
                                        print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                        print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                        print(f"Quantity: {product['quantity']}")
                                        print(f"Barcode: {product['barcode']}")
                                        print(f"Price: {product['price']}")
                                        print(f"Description: {product['description']}")
                                        print("-" * 40)

                            should_break = False
                            while True and not should_break:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to buy (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                                
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:

                                            for product3 in get_products():
                                                if product3['barcode'] == barcode:
                                                    if product3['description'] == "material":
                                                        print("you entered the barcode of a material, you can't buy material.")
                                                        continue
                                                    else:
                                                        should_break = True
                                                        break
                                        else:
                                            print(" Product with this barcode doesn't exist.")

                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_product(barcode)
                            quantity2=s_product['quantity']
                            addr1 = s_product['manufacturer']

                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the Product you want to buy: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the Product you want to buy.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Buying  Product")
                            sell_product(addr1,barcode,log_address,quantity)
                            
                            
                        elif num==4:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                            print("Enter the address of the buyer.")
                            address2 = get_address()
                            if check_user_exists(address2) == 0:
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)
                                print("User with this address exists with name: %s" %name2)
                            else:
                                print("You have to add the buyer in order to make a sale.")
                                make_buyer(address2,3,log_address)
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)

                            
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to sell (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        barcode=str(barcode)
                                        if checkDistributorProductBarcode(barcode)==1:
                                            break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                            continue
           
                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_distributor_product(barcode)
                            quantity2=s_product['quantity']

                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the product you want to sell: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the product you want to sell.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Selling product")
                            sell_product(log_address,barcode,address2,quantity)

                        elif num==5:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['from']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40)


                        elif num==6:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['to']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40)

                        elif num==7:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                print(f"\nReceipt #{i}:")
                                print(f"Id of receipt: {receipt['receiptId']}")
                                print(f"Wallet of Seller: {receipt['from']}")
                                print(f"Wallet of Buyer: {receipt['to']}")
                                print(f"Barcode of the product: {receipt['productBarcode']}")
                                status=return_receipt_status(receipt['status'])
                                print(f"Delivery status of product: {status}")
                                print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                print(f"Product quantity: {receipt['quantity']}")
                                print("-" * 40)

                        elif num==8:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet, so no receipts available yet.")
                                continue
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the sold product (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        receipts_count = get_receipt_count()
                                        if receipts_count==0:
                                            print("\nAll receipts are resolved.")
                                            continue
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            barcode=str(barcode)
                                            one_receipt = select_receipt(barcode)
                                            if one_receipt:
                                                if Web3.to_checksum_address(one_receipt['to']) == Web3.to_checksum_address(log_address):
                                                    if one_receipt['delivered']:
                                                        print("Receipt is already resolved")
                                                        break
                                                    else:
                                                        resolve_receipt(one_receipt['to'], one_receipt['receiptId'], barcode)
                                                    if one_receipt:
                                                        print("You selected the receipt with ID:", one_receipt['receiptId'])
                                                    break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                            
          
                                
                        elif num==9:
                            # find a user
                            address = get_address()
                            print(f"\n \nFinding User...")
                            print_user(address)

                        elif num==10:
                            break

        #------------------------------------------------------------------------------------------------------------------------------------
                elif role==3:
                    print("User is a Retailer.")


                    while True:
                        print("-" * 40)
                        print("\n1.) Add a buyer. ")
                        print("\n2.) Show all available products. ")
                        print("\n3.) Buy a product ")
                        print("\n4.) Sell a product ")
                        print("\n5.) Print all receipts for the products you sold. ")
                        print("\n6.) Print all receipts for the products you buyed. ")
                        print("\n7.) Print all receipts. ")
                        print("\n8.) Resolve a receipt if a product reached its destination. ")
                        print("\n9.) Find a user from address. ")
                        print("\n10.) Log out. ")
                        print("-" * 40)
                        while True:
                            try:
                                num  = int(input("Enter a number 1 through 10: "))
                                if num>10 or num<1:
                                    print("\nWrong input number")
                                else:
                                    break
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")

                        if num==1:               
                            print("Enter the wallet address of the new buyer: ")
                            address = get_address()
                            if check_user_exists(address) == 0:
                                print("Buyer already exists.")
                                continue
                            make_buyer(address,4,log_address)
                                

                                
                        elif num==2:
                            print("All Available Products:")
                            for product in get_distributor_products():
                                print("-" * 40)
                                print(f"\nName: {product['name']}")
                                print(f"Manufacturer Name: {product['manufacturerName']}")
                                print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"Quantity: {product['quantity']}")
                                print(f"Barcode: {product['barcode']}")
                                print(f"Price: {product['price']}")
                                print(f"Description: {product['description']}")
                                print("-" * 40)
                            
                        elif num==3:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)

                            counter=0
                            product2=get_distributor_products()
                            if len(product2)==0:
                                counter=1
                            if counter==1:
                                print("There are no available products to buy.")
                                continue

                            mat  = str(input("Enter y or Y if you want to see all available products: "))
                            if mat=="y" or mat=="Y":
                                print("All Products:")
                                for product in get_distributor_products():
                                    if product['description'] != "material":
                                        print("-" * 40)
                                        print(f"\nName: {product['name']}")
                                        print(f"Manufacturer Name: {product['manufacturerName']}")
                                        print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                        print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                        print(f"Quantity: {product['quantity']}")
                                        print(f"Barcode: {product['barcode']}")
                                        print(f"Price: {product['price']}")
                                        print(f"Description: {product['description']}")
                                        print("-" * 40)


                            should_break = False
                            while True and not should_break:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to buy (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                                
                                        barcode=str(barcode)
                                        if checkDistributorProductBarcode(barcode)==1:
                                            break
                                        else:
                                            print(" Product with this barcode doesn't exist.")

                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            print(barcode)

                            s_product = get_singular_distributor_product(barcode)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if receipt['productBarcode']==barcode:
                                    if desired_role(receipt['to'])==2:
                                        addr1 = receipt['to']
                                        break
                                    
                            quantity2=s_product['quantity']


                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the Product you want to buy: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the Product you want to buy.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Buying  Product")
                            sell_product(addr1,barcode,log_address,quantity)
                            
                            
                        elif num==4:
                            while True:
                                try:
                                    role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)
                                    print("Enter the address of the buyer.")
                                    address2 = get_address()
                                    if check_user_exists(address2) == 0:
                                        role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)
                                        print("User with this address exists with name: %s" %name2)
                                        if role2==4:
                                            break
                                        else:
                                            print("User isn't a customer")
                                    else:
                                        print("You have to add the buyer in order to make a sale.")
                                        make_buyer(address2,4,log_address)
                                except ValueError:      
                                    print("\nSorry, something went wrong.")

                                        
                                role2, userId2_, name2, physAdress2, phoneNumber2, email2=find_user(address2)

                            
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to sell (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        barcode=str(barcode)
                                        if checkRetailerProductBarcode(barcode)==1:
                                            break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                            continue
           
                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_retailer_product(barcode)
                            quantity2=s_product['quantity']

                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the product you want to sell: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the product you want to sell.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Selling product")
                            sell_product(log_address,barcode,address2,quantity)

                        elif num==5:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['from']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40)


                        elif num==6:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['to']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40)

                        elif num==7:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                print(f"\nReceipt #{i}:")
                                print(f"Id of receipt: {receipt['receiptId']}")
                                print(f"Wallet of Seller: {receipt['from']}")
                                print(f"Wallet of Buyer: {receipt['to']}")
                                print(f"Barcode of the product: {receipt['productBarcode']}")
                                status=return_receipt_status(receipt['status'])
                                print(f"Delivery status of product: {status}")
                                print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                print(f"Product quantity: {receipt['quantity']}")
                                print("-" * 40)

                        elif num==8:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet, so no receipts available yet.")
                                continue
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the sold product (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        receipts_count = get_receipt_count()
                                        if receipts_count==0:
                                            print("\nAll receipts are resolved.")
                                            continue
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            barcode=str(barcode)
                                            one_receipt = select_receipt(barcode)
                                            if one_receipt:
                                                if Web3.to_checksum_address(one_receipt['to']) == Web3.to_checksum_address(log_address):
                                                    if one_receipt['delivered']:
                                                        print("Receipt is already resolved")
                                                        break
                                                    else:
                                                        resolve_receipt(one_receipt['to'], one_receipt['receiptId'], barcode)
                                                    if one_receipt:
                                                        print("You selected the receipt with ID:", one_receipt['receiptId'])
                                                    break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                            
          
                                
                        elif num==9:
                            # find a user
                            address = get_address()
                            print(f"\n \nFinding User...")
                            print_user(address)

                        elif num==10:
                            break

        #------------------------------------------------------------------------------------------------------------------------------------
                elif role==4:
                    print("User is a Customer.")

                    while True:
                        print("-" * 40)
                        print("\n1.) Show all available products. ")
                        print("\n2.) Buy a product ")
                        print("\n3.) Print all receipts for the products you buyed. ")
                        print("\n4.) Print all receipts. ")
                        print("\n5.) Resolve a receipt if a product reached its destination. ")
                        print("\n6.) Find a user from address. ")
                        print("\n7.) Log out. ")
                        print("-" * 40)
                        while True:
                            try:
                                num  = int(input("Enter a number 1 through 7: "))
                                if num>7 or num<1:
                                    print("\nWrong input number")
                                else:
                                    break
                            except ValueError:      
                                print("\nSorry, that is not an integer. Please try again.")

                                
                        if num==1:
                            print("All Available Products:")
                            for product in get_retailer_products():
                                print("-" * 40)
                                print(f"\nName: {product['name']}")
                                print(f"Manufacturer Name: {product['manufacturerName']}")
                                print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"Quantity: {product['quantity']}")
                                print(f"Barcode: {product['barcode']}")
                                print(f"Price: {product['price']}")
                                print(f"Description: {product['description']}")
                                print("-" * 40)
                            
                        elif num==2:
                            role, userId_, name, physAdress, phoneNumber, email=find_user(log_address)

                            counter=0
                            product2=get_retailer_products()
                            if len(product2)==0:
                                counter=1
                            if counter==1:
                                print("There are no available products to buy.")
                                continue

                            mat  = str(input("Enter y or Y if you want to see all available products: "))
                            if mat=="y" or mat=="Y":
                                print("All Products:")
                                for product in get_retailer_products():
                                    if product['description'] != "material":
                                        print("-" * 40)
                                        print(f"\nName: {product['name']}")
                                        print(f"Manufacturer Name: {product['manufacturerName']}")
                                        print(f"Wallet address of manufacturer: {product['manufacturer']}")
                                        print(f"Made Date: {product['madeDate'].strftime('%Y-%m-%d %H:%M:%S')}")
                                        print(f"Quantity: {product['quantity']}")
                                        print(f"Barcode: {product['barcode']}")
                                        print(f"Price: {product['price']}")
                                        print(f"Description: {product['description']}")
                                        print("-" * 40)

                            should_break = False
                            while True and not should_break:
                                try:
                                    barcode  = int(input("Give the barcode of the product you want to buy (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                                
                                        barcode=str(barcode)
                                        if checkRetailerProductBarcode(barcode)==1:

                                            for product3 in get_retailer_products():
                                                if product3['barcode'] == barcode:
                                                    if product3['description'] == "material":
                                                        print("you entered the barcode of a material, you can't buy material.")
                                                        continue
                                                    else:
                                                        should_break = True
                                                        break
                                        else:
                                            print(" Product with this barcode doesn't exist.")

                                        
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")

                            s_product = get_singular_retailer_product(barcode)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if receipt['productBarcode']==barcode:
                                    if desired_role(receipt['to'])==3:
                                        addr1 = receipt['to']
                                        break
                                    
                            quantity2=s_product['quantity']


                            while True:
                                try:
                                    quantity  = int(input("Give the quantity of the Product you want to buy: "))
                                    if quantity>quantity2:
                                        print("Not enough quantity from the Product you want to buy.")
                                        print("Maximum quantity is %d units." %quantity2)
                                    else:
                                        break
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                                    
                            print(f"Buying  Product")
                            sell_product(addr1,barcode,log_address,quantity)
                            


                        elif num==3:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                if  Web3.to_checksum_address(receipt['to']) == Web3.to_checksum_address(log_address):
                                    print(f"\nReceipt #{i}:")
                                    print(f"Id of receipt: {receipt['receiptId']}")
                                    print(f"Wallet of Seller: {receipt['from']}")
                                    print(f"Wallet of Buyer: {receipt['to']}")
                                    print(f"Barcode of the product: {receipt['productBarcode']}")
                                    status=return_receipt_status(receipt['status'])
                                    print(f"Delivery status of product: {status}")
                                    print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                    print(f"Product quantity: {receipt['quantity']}")
                                    print("-" * 40)

                        elif num==4:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet.")
                                continue
                            print("\nAll Receipts: ")
                            print("-" * 40)
                            for i, receipt in enumerate(get_all_receipts(), 1):
                                print(f"\nReceipt #{i}:")
                                print(f"Id of receipt: {receipt['receiptId']}")
                                print(f"Wallet of Seller: {receipt['from']}")
                                print(f"Wallet of Buyer: {receipt['to']}")
                                print(f"Barcode of the product: {receipt['productBarcode']}")
                                status=return_receipt_status(receipt['status'])
                                print(f"Delivery status of product: {status}")
                                print(f"Delivered: {'Yes' if receipt['delivered'] else 'No'}") 
                                print(f"Product quantity: {receipt['quantity']}")
                                print("-" * 40)

                        elif num==5:
                            receipts_count = get_receipt_count()
                            if receipts_count==0:
                                print("\nNo Product sold yet, so no receipts available yet.")
                                continue
                            while True:
                                try:
                                    barcode  = int(input("Give the barcode of the sold product (100000 to 999999): "))
                                    if barcode>999999 or barcode<100000:
                                        print("\nCan't enter this barcode.")
                                    else:
                                        receipts_count = get_receipt_count()
                                        if receipts_count==0:
                                            print("\nAll receipts are resolved.")
                                            continue
                                        barcode=str(barcode)
                                        if checkProductBarcode(barcode)==1:
                                            barcode=str(barcode)
                                            one_receipt = select_receipt(barcode)
                                            if one_receipt:
                                                if Web3.to_checksum_address(one_receipt['to']) == Web3.to_checksum_address(log_address):
                                                    if one_receipt['delivered']:
                                                        print("Receipt is already resolved")
                                                        break
                                                    else:
                                                        resolve_receipt(one_receipt['to'], one_receipt['receiptId'], barcode)
                                                    if one_receipt:
                                                        print("You selected the receipt with ID:", one_receipt['receiptId'])
                                                    break
                                        else:
                                            print("Product with this barcode doesn't exist.")
                                except ValueError:      
                                    print("\nSorry, that is not an integer. Please try again.")
                            
          
                                
                        elif num==6:
                            # find a user
                            address = get_address()
                            print(f"\n \nFinding User...")
                            print_user(address)

                        elif num==7:
                            break


        except Exception as e:
            print(f"Error: {str(e)}")
        #except:      
            #print("\nSorry, something went wrong.")




