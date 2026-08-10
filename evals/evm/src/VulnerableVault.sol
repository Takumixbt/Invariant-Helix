// SPDX-License-Identifier: MIT
// Synthetic fixture with DELIBERATE, documented vulnerabilities used to test the
// Solidity analyzer's detection rate. Never deploy this. Each bug is labelled with the
// lead the analyzer is expected to raise.
pragma solidity ^0.8.20;

interface IToken {
    function transfer(address to, uint256 amount) external returns (bool);
}

contract VulnerableVault {
    mapping(address => uint256) public balances;
    address[] public depositors;
    address public owner;
    address public treasury;
    uint256 public totalDeposits;
    uint256 public feeBps;
    bool public paused;

    // BUG 1: unprotected-initializer - no initializer modifier, callable repeatedly.
    function initialize(address _owner) external {
        owner = _owner;
        feeBps = 100;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        depositors.push(msg.sender);
    }

    // BUG 2: reentrancy - external call precedes the balance write (CEI violation).
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "insufficient");
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "send failed");
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
    }

    // BUG 3: missing-access-control - anyone can move the treasury address.
    function setTreasury(address _treasury) external {
        treasury = _treasury;
    }

    // BUG 4: tx-origin-auth - phishable authority check.
    function emergencyDrain() external {
        require(tx.origin == owner, "not owner");
        payable(owner).transfer(address(this).balance);
    }

    // BUG 5: precision-loss - division before multiplication truncates the fee.
    function feeFor(uint256 amount) public view returns (uint256) {
        return amount / 10000 * feeBps;
    }

    // BUG 6: unbounded-loop - depositors is attacker-growable via deposit().
    function payoutAll(uint256 perUser) external {
        require(msg.sender == owner, "not owner");
        for (uint256 i = 0; i < depositors.length; i++) {
            balances[depositors[i]] += perUser;
        }
    }
}
