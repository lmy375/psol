# Psol

`Psol` is a solana command-line tool written in python.

# Usage

```
python -m psol.cli
Welcome to the psol shell. Type `help` to list commands.

psol > 

# Load local IDL file.
psol > local_idl ~/oft.json
IDL loaded from ~/oft.json
Saved to ~/.psol/idl_cache/local/oft.json

# Fetch IDL from on-chain data or from solscan.
psol > fetch_idl JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
IDL found for JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4 from solscan


# Print json-parsed account info.
psol > account FEf59AJ5vbzXGkdZkZrV1pf1GHCaceG7MVC2FP1HN2Vg
{
  "lamports": 2039280,
  "data": "28ae2daa4d6f7fbb2919d452ede0f0c0fa071aef1dc5ee314079741f5bc5c6fd4aa031381f2ae5d43c2155491b9fa9acbf3733381083df2fd6685584428ce245000000000000000000000000000000000000000000000000000000000000000000000000...",
  "owner": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
  "executable": false,
  "rentEpoch": 18446744073709551615,
  "size": 165
}
---- Parsed ----
{
  "program": "spl-token",
  "parsed": {
    "info": {
      "isNative": false,
      "mint": "3joMReCCSESngJEpFLoKR2dNcChjSRCDtybQet5uSpse",
      "owner": "62Jqyqrbe6i6zhUEtDUCYR2qfnH6PcqKqaVLg7saMJ7N",
      "state": "initialized",
      "tokenAmount": {
        "amount": "0",
        "decimals": 6,
        "uiAmount": 0.0,
        "uiAmountString": "0"
      }
    },
    "type": "account"
  },
  "space": 165
}

# Decode account data by IDL.
psol > account 62Jqyqrbe6i6zhUEtDUCYR2qfnH6PcqKqaVLg7saMJ7N
{
  "lamports": 2442960,
  "data": "c3d76886b9c3f07200010000000000000028ae2daa4d6f7fbb2919d452ede0f0c0fa071aef1dc5ee314079741f5bc5c6fdd3833706b7dc4c84da31f07af7a850634ff9f09b11511f04ca4e993d6f73756b5aad76da514b6e1dcf11037e904dac3d375f52...",
  "owner": "CATLZdvDfQcK99YntCaeDs8o342HcXRP1R5t4yTT5dUw",
  "executable": false,
  "rentEpoch": 18446744073709551615,
  "size": 223
}
---- Parsed ----
{
  "oft_type": "OFTType.Native()",
  "ld2sd_rate": 1,
  "token_mint": "3joMReCCSESngJEpFLoKR2dNcChjSRCDtybQet5uSpse",
  "token_escrow": "FEf59AJ5vbzXGkdZkZrV1pf1GHCaceG7MVC2FP1HN2Vg",
  "endpoint_program": "76y77prsiCMvXMjuoZ5VRrhG5qYBrUMYTE5WgHqgjEn6",
  "bump": 253,
  "tvl_ld": 0,
  "admin": "E5HXsDP7RXHeNFNsvNg3yJxcw9hWxSWgG5L2Pusskwuw",
  "default_fee_bps": 0,
  "paused": false,
  "pauser": null,
  "unpauser": null
}

# Decode instruction data by IDL
psol > ix_decode 66fb14bb414b0c459675000000000000000000000000000055afe9e5b17b0cb6efc204fc1bcf01b24ca996531d71f1a1b3100000962722419e10000002000000000300a4bd1f00000000000000000000000000
{
  "data": {
    "params": {
      "dst_eid": 30102,
      "to": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 85, 175, 233, 229, 177, 123, 12, 182, 239, 194, 4, 252, 27, 207, 1, 178, 76, 169, 150, 83],
      "amount_ld": 18363702145309,
      "min_amount_ld": 18271883634582,
      "options": "0003",
      "compose_msg": null,
      "native_fee": 2080164,
      "lz_token_fee": 0
    }
  },
  "name": "send"
}

psol > 
```
