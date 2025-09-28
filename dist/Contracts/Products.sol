// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

//pragma abicoder v2;
//pragma experimental SMTChecker;




library Class{

    enum Status{
        Manufactured,
        Delivering_to_Supplier,
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

}





//contract that includes functions around products
contract ProductFuncs{
    mapping(bytes32  => bool) private nameExists;
    mapping(bytes32  => bool) private barcodeExists;
    mapping(bytes32  => Class.Product) internal products;
    mapping(bytes32  => bool) private SbarcodeExists;
    mapping(bytes32  => Class.Product) internal supplierProducts;
    mapping(bytes32  => bool) private DbarcodeExists;
    mapping(bytes32  => Class.Product) internal distributorProducts;
    mapping(bytes32  => bool) private RbarcodeExists;
    mapping(bytes32  => Class.Product) internal retailerProducts;
    mapping(bytes32  => bool) private CbarcodeExists;
    mapping(bytes32  => Class.Product) internal customerProducts;
    mapping(uint256 => Class.Receipt) internal ongoingReceipt;
    mapping(uint256 => Class.Receipt) internal resolvedReceipt;


    Class.Product[] public allProducts;
    bytes32[] public allProducts2;
    /*bytes32[] public  productKeys;*/
    bytes32[] private allresolved;
    bytes32[] private allongoing;


    event AddNewProduct(
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

    // only manufacturers can create products
    function createProduct(Class.Product memory newProduct_) public {
        // check if the address i puted in is the same as my address
        /*require(
            findUser(newProduct_.manufacturer).role == Class.UserRole.Manufacturer,
            "Only manufacturers can add products"
            /*newProduct_.manufacturer == msg.sender,
            "Only manufacturers can add products"
        );*/

        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(newProduct_.barcode));
        bytes32 key2 = keccak256(abi.encodePacked(newProduct_.name));

        // Check if product with the given name already exists
        require(!nameExists[key2], "Food with the same name already exists");

        // Check if product with the given barcode already exists
        require(!barcodeExists[key], "Food with the same barcode already exists");

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

    // function to sell a product
    function sellProduct(Class.UserIdentity memory user,string memory barcode,
        address buyerId_, uint256 quantity_ ) public {

        //we use hash function keccak256 to avoid problems with string keys     
        bytes32 key = keccak256(abi.encodePacked(barcode));

        // Check if product with the given barcode exists
        require(barcodeExists[key], "Product with the same barcode does not exists");

        // Require that the provided address is not the zero address
        require(buyerId_ != address(0), "Zero address");

        if (user.role == Class.UserRole.Manufacturer){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = products[key];
            if (product_.quantity>=quantity_){
                // first i lower the quantity of the original product and update
                product_.quantity = product_.quantity - quantity_;
                uint256 value = product_.quantity;
                products[key]=product_;
                // second i put the selled product with the requested quantity in a mapping
                product_.quantity = 0; //quantity_;
                supplierProducts[key] = product_;
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Supplier, barcode,quantity_,0);
                if (value==0){
                    delete products[key];
                }
            }
            else{
                emit CheckProductQuantity(product_.quantity);
                revert("not enough quantity");
            }
        }
        else if (user.role == Class.UserRole.Supplier){
            // Check if product with the given barcode exists in mapping
            require(SbarcodeExists[key], "Product with the same barcode does not exists");
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = supplierProducts[key];
            if (product_.quantity>=quantity_){
                // first i lower the quantity of the original product and update
                product_.quantity = product_.quantity - quantity_;
                uint256 value = product_.quantity;
                supplierProducts[key]=product_;
                // second i put the selled product with the requested quantity in a mapping
                product_.quantity = 0; //quantity_;
                distributorProducts[key] = product_;
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Supplier, barcode,quantity_,1);
                if (value==0){
                    delete supplierProducts[key];
                }
            }
            else{
                emit CheckProductQuantity(product_.quantity);
                revert("not enough quantity");
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
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Supplier, barcode,quantity_,2);
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
                issueReceipt(user.userId_, buyerId_, Class.Status.Delivering_to_Supplier, barcode,quantity_,3);
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
            supplierProducts[key] = product_;
            SbarcodeExists[key] = true;
            ongoingReceipt[resid].delivered=true;
        }
        else if (resReceipt.num==1){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = supplierProducts[key];
            product_.quantity = resReceipt.quantity;
            distributorProducts[key] = product_;
            DbarcodeExists[key] = true;
            ongoingReceipt[resid].delivered=true;
        }
        else if (resReceipt.num==2){
            //we take the product we want from the mapping in a tuple named product_
            Class.Product memory product_ = distributorProducts[key];
            product_.quantity = resReceipt.quantity;
            retailerProducts[key] = product_;
            RbarcodeExists[key] = true;  
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

    function printProducts() public view returns(Class.Product[] memory){
        return allProducts;
    }

    

    function getProduct(bytes32 key) public view returns (string memory,string memory,address,
        uint256,uint256,string memory,uint,string memory) {
        Class.Product memory d = products[key];
        return (d.name,d.manufacturerName,d.manufacturer,d.madeDate,d.quantity,
            d.barcode,d.price,d.description);
    }
    
}



//