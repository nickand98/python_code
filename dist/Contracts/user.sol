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

/*library HelpFuncs{

    //check if an account with an adress has a specific role
    function checkRole(Class.UserRole role, address account)
        internal view returns (bool)
    {
        // Require that the provided address is not the zero address
        require(account != address(0), "Zero address");

        // Returns True if this account has already the role
        return (User.users[account].userId_ != address(0) &&
            User.users[account].role == role);
    }

}*/

// contract that contains functions around users
contract User{
    mapping(address => Class.UserIdentity) internal users;
    mapping(address => Class.SellBuy[]) internal manufacturerAddSuppliers;
    mapping(address => Class.SellBuy[]) internal supplierAddDistributors;
    mapping(address => Class.SellBuy[]) internal distributorAddRetailers;
    mapping(address => Class.SellBuy[]) internal retailerAddCustomers;
    mapping(address => Class.UserIdentity[]) internal addedSuppliers;
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
        if (findUser(account).role == Class.UserRole.Manufacturer &&
            buyer.role == Class.UserRole.Supplier)
            {
                Class.SellBuy memory newSupplier = Class.SellBuy({
                    roleOne: Class.UserRole.Manufacturer,
                    from: account,
                    roleTwo: Class.UserRole.Supplier,
                    to: buyer.userId_
                });
                // adds the person to a mapping with the account as key
                addedSuppliers[account].push(buyer);
                //adds the SellBuy struct to a mapping with the account as key
                manufacturerAddSuppliers[account].push(newSupplier);
                addUser(buyer);
            }
        //only a Supplier can add Distributors
        else if (findUser(account).role == Class.UserRole.Supplier &&
            buyer.role == Class.UserRole.Distributor)
            {
                Class.SellBuy memory newDistributor = Class.SellBuy({
                    roleOne: Class.UserRole.Supplier,
                    from: account,
                    roleTwo: Class.UserRole.Distributor,
                    to: buyer.userId_
                });
                supplierAddDistributors[account].push(newDistributor);
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
        if (findUser(userId_).role == Class.UserRole.Manufacturer)
            {
            allBuyers = addedSuppliers[userId_];  
            }
        else if (findUser(userId_).role == Class.UserRole.Supplier)
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




//