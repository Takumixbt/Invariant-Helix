// SPDX-License-Identifier: MIT
// Synthetic fixture contract for x-ray enumeration tests. Not a real protocol.
pragma solidity ^0.8.20;

contract Vault {
    mapping(address => uint256) public shares;
    uint256 public totalShares;

    function deposit(uint256 amount) external {
        uint256 minted = totalShares == 0 ? amount : amount * totalShares / address(this).balance;
        shares[msg.sender] += minted;
        totalShares += minted;
    }

    function withdraw(uint256 amount) external {
        shares[msg.sender] -= amount;
        totalShares -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
    }

    function rewardDebt(address account) public view returns (uint256) {
        return shares[account];
    }
}
