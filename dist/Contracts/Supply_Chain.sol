// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

//pragma abicoder v2;
//pragma experimental SMTChecker;




library Class{

    enum Status{
        Manufactured,
        Delivering_to_Manufacturer,
        Delivering_to_Distributor,
        Delivering_to_Retailer,
        Delivering_to_Customer
    }

    enum UserRole {
        Manufacturer, // 0 
        Supplier, // 1
        Distributor, // 2
        Retailer, // 3
        Customer // 4
    }

    struct UserIdentity {
        UserRole role;
        address userId_;
        string name;
        string physAdress;
        string phoneNumber;
        string email;
    }

    struct Receipt {
        uint256 receiptId;
        address from;
        address to;
        string productBarcode;
        Status status;
        bool delivered;
        uint256 quantity;
        uint256 num;
        
    }

    struct SellBuy {
        UserRole roleOne;
        address from;
        UserRole roleTwo;
        address to;
    }

    struct Product {
        string name;
        string manufacturerName;
        address manufacturer;
        uint256 madeDate;
        uint256 quantity;
        string barcode;
        uint price;
        string description;
    }

    /*struct material {
        string name;
        string supplierName;
        //address supplier;
        //uint256 madeDate;
        uint256 quantity;
        string barcode;
        uint price;
        string description;
    }*/

}

// contract that contains functions around users
contract User{
    mapping(address => Class.UserIdentity) internal users;
    mapping(address => Class.SellBuy[]) internal supplierAddManufacturer;
    mapping(address => Class.SellBuy[]) internal manufacturerAddDistributors;
    mapping(address => Class.SellBuy[]) internal distributorAddRetailers;
    mapping(address => Class.SellBuy[]) internal retailerAddCustomers;
    mapping(address => Class.UserIdentity[]) internal addedManufacturers;
    mapping(address => Class.UserIdentity[]) internal addedDistributors;
    mapping(address => Class.UserIdentity[]) internal addedRetailers;
    mapping(address => Class.UserIdentity[]) internal addedCustomers;

    event NewUser(Class.UserIdentity user);
    event LeavingUser(Class.UserRole role,string name);

    //check if an account with an adress has a specific role
    function checkRole(Class.UserRole role, address account)
        internal view returns (bool)
    {
        // Require that the provided address is not the zero address
        require(account != address(0), "Zero address");

        // Returns True if this account has already the role
        return (users[account].userId_ != address(0) &&
            users[account].role == role);
    }

    //function to add a new user
    function addUser(Class.UserIdentity memory newUser) public {
        // Require that the provided address is not the zero address
        require(newUser.userId_ != address(0), "Zero address");

        // Require that the provided address and role do not already exist
        require(!checkRole(newUser.role, newUser.userId_), "User exists");

        // Store the new user details in the mapping
        users[newUser.userId_] = newUser;

        // Emit the NewUser event to log the new user's information
        emit NewUser(newUser);
    }

    //function to remove a user
    function deleteUser(Class.UserRole role, address account) internal {
        // Require that the provided address is not the zero address
        require(account != address(0), "Zero address");

        // Require that the provided address and role do not already exist
        require(!checkRole(role, account), "User exists");

        // Save the name before deleting the user
        string memory name_ = users[account].name;

        delete users[account];

        //emit the event with the role and name of the user deleted
        emit LeavingUser(role,name_);
    }

    //function that returns the user with the given address
    function findUser(address userid) public view returns(Class.UserIdentity memory){
        // Require that the provided address is not the zero address
        require(userid != address(0), "Zero address");

        // returns the user i want from the mapping
        return users[userid];
    }

    //adds a user to sell products to
    function addBuyer(Class.UserIdentity memory buyer, address account) public {
        // Require that the provided address is not the zero address
        require(account != address(0), "Zero address");
        require(buyer.userId_ != address(0), "Zero address");
        
        //only a manufacturer can add suppliers
        if (findUser(account).role == Class.UserRole.Supplier &&
            buyer.role == Class.UserRole.Manufacturer)
            {
                Class.SellBuy memory newManufacturer = Class.SellBuy({
                    roleOne: Class.UserRole.Supplier,
                    from: account,
                    roleTwo: Class.UserRole.Manufacturer,
                    to: buyer.userId_
                });
                // adds the person to a mapping with the account as key
                addedManufacturers[account].push(buyer);
                //adds the SellBuy struct to a mapping with the account as key
                supplierAddManufacturer[account].push(newManufacturer);
                addUser(buyer);
            }
        //only a Supplier can add Distributors
        else if (findUser(account).role == Class.UserRole.Manufacturer &&
            buyer.role == Class.UserRole.Distributor)
            {
                Class.SellBuy memory newDistributor = Class.SellBuy({
                    roleOne: Class.UserRole.Manufacturer,
                    from: account,
                    roleTwo: Class.UserRole.Distributor,
                    to: buyer.userId_
                });
                manufacturerAddDistributors[account].push(newDistributor);
                addedDistributors[account].push(buyer);
                addUser(buyer);

            }
        //only a Distributor can add Retailers
        else if (findUser(account).role == Class.UserRole.Distributor &&
            buyer.role == Class.UserRole.Retailer)
            {
                Class.SellBuy memory newRetailer = Class.SellBuy({
                    roleOne: Class.UserRole.Distributor,
                    from: account,
                    roleTwo: Class.UserRole.Retailer,
                    to: buyer.userId_
                });
                distributorAddRetailers[account].push(newRetailer);
                addedRetailers[account].push(buyer);
                addUser(buyer);

            }
        //only a Retailer can add Customers
        else if (findUser(account).role == Class.UserRole.Retailer &&
            buyer.role == Class.UserRole.Customer)
            {
                Class.SellBuy memory newCustomer = Class.SellBuy({
                    roleOne: Class.UserRole.Retailer,
                    from: account,
                    roleTwo: Class.UserRole.Customer,
                    to: buyer.userId_
                });
                retailerAddCustomers[account].push(newCustomer);
                addedCustomers[account].push(buyer);
                addUser(buyer);
            }
        else{
            revert("Somethig went wrong");
        }
    }
    
    // returns the buyers that the person with the given address added
    function findAllBuyers(address userId_) internal view 
    returns(Class.UserIdentity[] memory allBuyers){
        // Require that the provided address is not the zero address
        require(userId_ != address(0), "Zero address");
        if (findUser(userId_).role == Class.UserRole.Supplier)
            {
            allBuyers = addedManufacturers[userId_];  
            }
        else if (findUser(userId_).role == Class.UserRole.Manufacturer)
            {
            allBuyers = addedDistributors[userId_];  
            }
        else if (findUser(userId_).role == Class.UserRole.Distributor)
            {
            allBuyers = addedRetailers[userId_];  
            }
        else if (findUser(userId_).role == Class.UserRole.Retailer)
            {
            allBuyers = addedCustomers[userId_];  
            }
        else{
            revert("Somethig went wrong");
        }
    }
}

//contract that includes functions around products
contract ProductFuncs{
    mapping(bytes32  => bool) private nameExists;
    mapping(bytes32  => bool) private barcodeExists;
    mapping(bytes32  => Class.Product) internal products;
    mapping(bytes32  => Class.Product) internal manufacturerMaterials;
    mapping(bytes32  => bool) private MbarcodeExists;
    mapping(bytes32  => Class.Product) internal supplierProducts;
    mapping(bytes32  => bool) private DbarcodeExists;
    mapping(bytes32  => Class.Product) public distributorProducts;
    mapping(bytes32  => bool) private RbarcodeExists;
    mapping(bytes32  => Class.Product) public retailerProducts;
    mapping(bytes32  => bool) private CbarcodeExists;
    mapping(bytes32  => Class.Product) internal customerProducts;
    mapping(uint256  => Class.Receipt) internal ongoingReceipt;
    mapping(uint256  => Class.Receipt) internal resolvedReceipt;

    Class.Product[] public allProducts;
    bytes32[] public allProducts2;
    bytes32[] private allresolved;
    bytes32[] private allongoing;
    bytes32[] public Rkeys;
    bytes32[] public Dkeys;


    event AddNewProduct(
        string name,
        string manufacturerName,
        uint256 madeDate,
        uint256 quantity,
        string barcode,
        uint price
    );

    event AddNewMaterial(
        string name,
        string manufacturerName,
        uint256 madeDate,
        uint256 quantity,
        string barcode,
        uint price
    );

    event ReceiptIdShow(uint256 receiptId);

    event CheckProductQuantity(uint256 quantity);

    function checkProductName(string memory name) public view returns (uint256){
        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key2 = keccak256(abi.encodePacked(name));

        // Check if product with the given name already exists
        if (!nameExists[key2]){
            return 0;
        }
        else{
            return 1;
        }
    }


    function checkProductBarcode(string memory barcode) public view returns (uint256){

        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(barcode));

        // Check if product with the given barcode already exists
        if (!barcodeExists[key]){
            return 0;
        }
        else{
            return 1;
        }
    }


    // only manufacturers can create products and suppliers can put materials 
    function createProduct(Class.Product memory newProduct_) public {
      
        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(newProduct_.barcode));
        bytes32 key2 = keccak256(abi.encodePacked(newProduct_.name));

        // Check if product with the given name already exists
        require(!nameExists[key2], "Product or material with the same name already exists");
        // Check if product with the given barcode already exists
        require(!barcodeExists[key], "Product or material with the same barcode already exists");

        //we push the product to an array
        allProducts.push(newProduct_);
        allProducts2.push(key);
        /*productKeys = keccak256(abi.decodePacked(newProduct_.barcode));*/
        // Add the new product to the mappings
        nameExists[key2] = true;
        barcodeExists[key] = true;
        products[key] = newProduct_;
        

        emit AddNewProduct(
            newProduct_.name,
            newProduct_.manufacturerName,
            newProduct_.madeDate,
            newProduct_.quantity,
            newProduct_.barcode,
            newProduct_.price
        );
    }

    /*// only suppliers can put materials
    function putMaterial(Class.Product memory newProduct_) public {


        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(newProduct_.barcode));
        bytes32 key2 = keccak256(abi.encodePacked(newProduct_.name));

        // Check if product with the given name already exists
        require(!nameExists[key2], "Material with the same name already exists");

        // Check if product with the given barcode already exists
        require(!barcodeExists[key], "Material with the same barcode already exists");

        //we push the product to an array
        Class.Product memory newProduct2_ = Class.Product({
            name: newProduct_.name,
            manufacturerName: newProduct_.manufacturerName,
            manufacturer: newProduct_.manufacturer,
            madeDate: newProduct_.madeDate,
            quantity: newProduct_.quantity,
            barcode: newProduct_.barcode,
            price: newProduct_.price,
            description: "material"
        });
        allProducts.push(newProduct2_);
        allProducts2.push(key);

        // Add the new product to the mappings
        nameExists[key2] = true;
        barcodeExists[key] = true;
        products[key] = newProduct_;

        emit AddNewMaterial(
            newProduct2_.name,
            newProduct2_.manufacturerName,
            newProduct2_.madeDate,
            newProduct2_.quantity,
            newProduct2_.barcode,
            newProduct2_.price
        );
    }*/

    // function to sell a product
    function sellProduct(Class.UserIdentity memory user,string memory barcode,
        address buyerId_, uint256 quantity_ ) public {

        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(barcode));

        require(barcodeExists[key], "Product with the same barcode does not exists");

        // Require that the provided address is not the zero address
        require(buyerId_ != address(0), "Zero address");

        if (user.role == Class.UserRole.Manufacturer){
            // Check if product with the given barcode exists

            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = products[key];
            if (product_.quantity>=quantity_){
                // first i lower the quantity of the original product and update
                product_.quantity = product_.quantity - quantity_;
                products[key]=product_;
                // second i put the selled product with the requested quantity in a mapping
                product_.quantity = 0; //quantity_;
                distributorProducts[key] = product_;
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Distributor, barcode,quantity_,0);

            }
            else{
                emit CheckProductQuantity(product_.quantity);
                revert("not enough quantity");
            }
        }
        else if (user.role == Class.UserRole.Supplier){

            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = products[key];
            if (keccak256(abi.encodePacked(product_.description)) == keccak256(abi.encodePacked("material"))){
                if (product_.quantity>=quantity_){
                    // first i lower the quantity of the original product and update
                    product_.quantity = product_.quantity - quantity_;
                    supplierProducts[key]=product_;
                    // second i put the selled product with the requested quantity in a mapping
                    product_.quantity = 0; //quantity_;
                    manufacturerMaterials[key] = product_;
                    issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Manufacturer, barcode,quantity_,1);
                }
                else{
                    emit CheckProductQuantity(product_.quantity);
                    revert("not enough quantity");
                }
            }
            else{
                revert("This isn't a material");
            }
        }
        else if (user.role == Class.UserRole.Distributor){
            // Check if product with the given barcode exists in mapping
            require(DbarcodeExists[key], "Product with the same barcode does not exists");
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = distributorProducts[key];
            if (product_.quantity>=quantity_){
                // first i lower the quantity of the original product and update
                product_.quantity = product_.quantity - quantity_;
                uint256 value = product_.quantity;
                distributorProducts[key]=product_;
                // second i put the selled product with the requested quantity in a mapping
                product_.quantity = 0; //quantity_;
                retailerProducts[key] = product_;
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Retailer, barcode,quantity_,2);
                if (value==0){
                    delete distributorProducts[key];
                }
            }
            else{
                emit CheckProductQuantity(product_.quantity);
                revert("not enough quantity");
            } 
        }
        else if (user.role == Class.UserRole.Retailer){
            // Check if product with the given barcode exists in mapping
            require(RbarcodeExists[key], "Product with the same barcode does not exists");
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = retailerProducts[key];
            if (product_.quantity>=quantity_){
                // first i lower the quantity of the original product and update
                product_.quantity = product_.quantity - quantity_;
                uint256 value = product_.quantity;
                retailerProducts[key]=product_;
                // second i put the selled product with the requested quantity in a mapping
                product_.quantity = 0; //quantity_;
                customerProducts[key] = product_;
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Customer, barcode,quantity_,3);
                if (value==0){
                    delete retailerProducts[key];
                }
            }
            else{
                emit CheckProductQuantity(product_.quantity);
                revert("not enough quantity");
            }  
        }
        else{
            revert("Somethig went wrong");
        }
    }

    uint256 public myNumber;
    //function that creates the receipts when selling products
    function issueReceipt(address sellerid_,address buyerid_,Class.Status status_,string memory barcode_,uint256 quantity_,uint256 num_) internal {

        // Require that the provided address is not the zero address
        require(sellerid_ != address(0), "Zero address");
        // Require that the provided address is not the zero address
        require(buyerid_ != address(0), "Zero address");

        myNumber=allongoing.length+1;
        //add the receipt to the mappings
        Class.Receipt memory newReceipt = Class.Receipt(myNumber,sellerid_,buyerid_,barcode_,status_,false,quantity_,num_);
        ongoingReceipt[myNumber] = newReceipt;
        bytes32 key2 = keccak256(abi.encodePacked(sellerid_));
        allongoing.push(key2);

        emit ReceiptIdShow(newReceipt.receiptId);
    
    }

    // when the product reach the buyer we show it was delivered 
    function resolveReceipt(address buyerid_,uint256 resid,string memory barcode_) public {

        // Require that the provided address is not the zero address
        require(buyerid_ != address(0), "Zero address");

        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(barcode_));

        //finds the receipt of the product that was delivered and adds to a new
        //mapping with the delivered bool -> true
        Class.Receipt memory resReceipt = ongoingReceipt[resid] ;
        resReceipt.delivered=true;
        resolvedReceipt[resid] = resReceipt;
        bytes32 key2 = keccak256(abi.encodePacked(buyerid_));
        allresolved.push(key2);

        if (resReceipt.num==0){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = products[key];
            //we had the quantity at zero until the product reached its destination
            product_.quantity = resReceipt.quantity;
            // a bool mapping that we use to point that a barcode exists in the suppliers products mapping

            distributorProducts[key] = product_;
            DbarcodeExists[key] = true;
            Dkeys.push(key);
            ongoingReceipt[resid].delivered=true;
        }
        else if (resReceipt.num==1){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = supplierProducts[key];
            product_.quantity = resReceipt.quantity;
            manufacturerMaterials[key] = product_;
            MbarcodeExists[key] = true;
            ongoingReceipt[resid].delivered=true;
        }
        else if (resReceipt.num==2){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = distributorProducts[key];
            product_.quantity = resReceipt.quantity;
            retailerProducts[key] = product_;
            RbarcodeExists[key] = true;  
            Rkeys.push(key);
            ongoingReceipt[resid].delivered=true;      
        }
        else if (resReceipt.num==3){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = retailerProducts[key];
            product_.quantity = resReceipt.quantity;
            customerProducts[key] = product_;
            CbarcodeExists[key] = true; 
            ongoingReceipt[resid].delivered=true;         
        }
        else{
            revert("Somethig went wrong");
        }
        
    }
    
    //help functions that show how many products and receipts we have
    function getProductCount() public view returns (uint256) {
        return allProducts2.length;
    }
    function getReceiptCount() public view returns (uint256) {
        return allongoing.length;
    }
    function getResolvedReceiptCount() public view returns (uint256) {
        return allresolved.length;
    }

    // functions we can use to cycle through each product and receipt
    function getReceiptByIndex(uint256 index) public view returns (Class.Receipt memory) {
        require(index < allongoing.length, "Invalid index");

        uint receiptkey = index+1;
        return ongoingReceipt[receiptkey];
    }

    function getResolvedReceiptByIndex(uint256 index) public view returns (Class.Receipt memory) {
        require(index < allresolved.length, "Invalid index");

        uint resolvedReceiptkey = index+1;
        return resolvedReceipt[resolvedReceiptkey];
    }

    /*// Function to get Product details by index
    function getProductByIndex(uint256 index) public view returns (Class.Product memory) {
        require(index < allProducts2.length, "Invalid index");

        bytes32 productKey = allProducts2[index];
        return products[productKey];
    }*/

    function getProductKeys() public view returns (bytes32[] memory){    
        return allProducts2; 
    }

    /*function printProducts() public view returns(Class.Product[] memory){
        return allProducts;
    }*/

    

    function getProduct(bytes32 key) public view returns (string memory,string memory,address,
        uint256,uint256,string memory,uint,string memory) {
        Class.Product memory d = products[key];
        return (d.name,d.manufacturerName,d.manufacturer,d.madeDate,d.quantity,
            d.barcode,d.price,d.description);
    }
    function getDistributorProducCount() public view returns (uint256) {
        return Dkeys.length;
    }
    function getRetailerProducCount() public view returns (uint256) {
        return Rkeys.length;
    }

}

// the main contract that calls functions from other products
contract Supplychain{

    User public myuser;
    ProductFuncs public myproduct;
    constructor(address userAddress,address productAddress) {
        myuser = User(userAddress);
        myproduct = ProductFuncs(productAddress);

    }

    function addauser(Class.UserIdentity memory user) external {
        myuser.addUser(user);
    }
    function addaproduct(Class.Product memory product) external {
        myproduct.createProduct(product);
    }
    function findaUser(address userid) public view returns(Class.UserIdentity memory) {
        return myuser.findUser(userid);
    }
    
    function addAbuyer(Class.UserIdentity memory buyer, address account) internal {
        myuser.addBuyer(buyer, account);
    }
    /*function getDistributorProduct(bytes32 key) public view returns (string memory,string memory,address,
        uint256,uint256,string memory,uint,string memory) {
        return myproduct.distributorProducts(key);
    }/*
    /*function getRetailerProduct(bytes32 key) public view returns (string memory,string memory,address,
        uint256,uint256,string memory,uint,string memory) {
        return myproduct.getretailerProducts(key);
    }*/


    function sellaProduct(address sellerId_,string memory barcode,
        address buyerId_, uint256 quantity_ ) public {
            require(sellerId_ != address(0), "Zero address");
            require(buyerId_ != address(0), "Zero address");
            Class.UserIdentity memory user = myuser.findUser(sellerId_);
            Class.UserIdentity memory userb = myuser.findUser(buyerId_);
            
            if (user.role == Class.UserRole.Manufacturer && userb.role == Class.UserRole.Distributor){
                myproduct.sellProduct(user, barcode, buyerId_, quantity_);
            }
            else if (user.role == Class.UserRole.Supplier && userb.role == Class.UserRole.Manufacturer){
                myproduct.sellProduct(user, barcode, buyerId_, quantity_);

            }
            else if (user.role == Class.UserRole.Distributor && userb.role == Class.UserRole.Retailer){
                myproduct.sellProduct(user, barcode, buyerId_, quantity_);
            }
            else if (user.role == Class.UserRole.Retailer && userb.role == Class.UserRole.Customer){
                myproduct.sellProduct(user, barcode, buyerId_, quantity_);
            }
            else{

                revert("sale failed");

            }
            
    }
    function resolveAReceipt(address buyerid_,uint256 resid,string memory barcode_) public {
        myproduct.resolveReceipt(buyerid_,resid, barcode_);
    }

    function getProductCount() public view returns (uint256){
        myproduct.getProductCount();
        return myproduct.getProductCount();
    }
    function getAReceiptCount() public view returns (uint256) {
        myproduct.getReceiptCount();
        return myproduct.getReceiptCount();
    }
    function getAResolvedReceiptCount() public view  returns (uint256){
        myproduct.getResolvedReceiptCount();
        return myproduct.getResolvedReceiptCount();
    }

    function getAReceiptByIndex(uint256 index) public view returns (Class.Receipt memory){
        myproduct.getReceiptByIndex(index);
        return myproduct.getReceiptByIndex(index);
    }

    function getAResolvedReceiptByIndex(uint256 index) public view returns (Class.Receipt memory) {
        myproduct.getResolvedReceiptByIndex(index);
        return myproduct.getResolvedReceiptByIndex(index);
    }

    /*function getAProductByIndex(uint256 index) internal view returns (Class.Product memory){
        myproduct.getProductByIndex(index);
        return myproduct.getProductByIndex(index);
    }*/

    function printAllProducts() public view returns(Class.Product[] memory){
      
        uint256 count = getProductCount();
        Class.Product[] memory products = new Class.Product[](count);

        for (uint256 i = 0; i < count; i++) {
            
            (string memory name,string memory manufacturerName,address manufacturer,
                uint256 madeDate,uint256 quantity,string memory barcode,uint256 price,string memory description) = myproduct.allProducts(i);

            products[i] = Class.Product(name,manufacturerName, manufacturer,madeDate,quantity,
            barcode,price,description);
        }
        return products;
    }

/*function getDistributorProducts() public view returns (string[] memory ,string[] memory ,address[] ,
                uint256[] ,uint256[] ,string[] memory ,uint256[] ,string[] memory ) {
    uint256 count = myjohn.getColdFoodCount();
    
    string[] memory names = new string[](count);
    address[] memory creators = new address[](count);
    string[] memory ids = new string[](count);
    
    for (uint256 i = 0; i < count; i++) {
        // Get the key from the array
        bytes32 foodKey = myjohn.allColdFoodKeys(i);
        
        // Get the food data from the mapping
        (string memory name, address creator, string memory id) = myproduct.di(foodKey);
        
        names[i] = name;
        creators[i] = creators;
        ids[i] = id;
    }
    
    return (names, creators, ids);
}*/

function getDistributorProductByKey(bytes32 key) public view returns (string memory ,string memory ,address ,
                uint256 ,uint256 ,string memory ,uint256 ,string memory) {
    return myproduct.distributorProducts(key);
}

function getRetailerProductByKey(bytes32 key) public view returns (string memory ,string memory ,address ,
                uint256 ,uint256 ,string memory ,uint256 ,string memory) {
    return myproduct.retailerProducts(key);
}


}



//