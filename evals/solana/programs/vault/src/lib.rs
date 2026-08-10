// Synthetic fixture Anchor program for x-ray chain-neutrality tests. Not real.
use anchor_lang::prelude::*;

declare_id!("Fixture1111111111111111111111111111111111111");

#[program]
pub mod vault {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, seed: u64) -> Result<()> {
        ctx.accounts.state.total_shares = 0;
        ctx.accounts.state.seed = seed;
        Ok(())
    }

    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        ctx.accounts.state.total_shares = ctx.accounts.state.total_shares.checked_add(amount).unwrap();
        Ok(())
    }

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        ctx.accounts.state.total_shares = ctx.accounts.state.total_shares.checked_sub(amount).unwrap();
        Ok(())
    }
}
