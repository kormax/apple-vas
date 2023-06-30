# Apple VAS


# Overview

Apple VAS (Value-added services) is a proprietary NFC protocol that can be used for sending data from a mobile device to an NFC terminal.

Apart from reading passes, this protocol also allows reader to send a signup URL to the device, causing a signup link notification to appear on devices that do not have an appropriate pass downloaded.

Pass data is transmitted in encrypted form. Shared key is derived via ECDH exchange and is single use only.

Depending on opreation mode, one or multiple passes can be read in a single tap.

Version 1 was current at the time of writing.


# Application identifiers


VAS can be activated using following application id (AID):

1. VAS AID (hex of encoded 'OSE.VAS.01'), also used by Google Smart Tap.  
    ```
    4f53452e5641532e3031
    ```

The ususal implementation for most readers is to select OSE.VAS.01 in order to detect what wallet provider is available on device (stored in TLV tag 50), if "ApplePay" is the value, then we have a device with Apple Wallet.


# Modes

## Operation modes

Apple VAS has multiple operation modes. Mode setting affects:
* How the system UI will react to the transaction.
* If you are allowed to read multiple different passes in one tap.
  
Following modes are available:
1. VAS or payment:  
   Operates the same as VAS and payment (Info below). Can also be called VAS over payment, meaning that a reader tries to read a loyalty pass, if it has enough balance it ends the transaction.  Otherwise it tries to charge the selected payment card.
2. VAS and payment:  
   Also called single tap mode. In this mode reader should select a VAS applet, read loyatly info, and after that select a payment applet and finish a transaction. **This mode supports reading multiple different passes in a single tap**, although UI will only tell about the first one. In this mode bringing the device to the field will display a default payment card, after auth it will also display that "Pass X will be also used" under the card.  
   <img src="./assets/VAS.MODE.VASANDPAY.webp" alt="![VAS and payment]" width=200px>
3. VAS only:  
   Used when you only need to read a pass. In this mode if a phone is brought into the field before auth it will present the needed pass on the screen for authentication. **This mode allows to read only one pass at a time**. If you preauthenticate a payment card, a needed pass will jump in place of a payment card when you bring the device to the reader.  
   <img src="./assets/VAS.MODE.VASONLY.BEFORE.AUTH.webp" alt="![VAS and payment]" width=200px>
4. Payment only:
   Serves as anti-CATHAY.

## Protocol modes

VAS also has a protocol MODE flag.

1. URL:  
   Value 0x00. In this mode the reader works as a signup terminal. Tapping a device to it will display a sign-up notification on the screen.
2. FULL:  
   Value 0x01. Can be used for both pass redemption and URL signup advertisment.

# Commands

As of version 1 following commands are available:

| Command name | CLA | INS | P1  | P2   | DATA    | LE  | Notes                       |
| ------------ | --- | --- | --- | ---- | ------- | --- | --------------------------- |
| Select VAS   | 00  | A4  | 04  | 00   | VAS AID | 00  |                             |
| Get data     | 80  | CA  | 01  | MODE | *       | 00  | Data format described below |


# Command and response data format

VAS uses TLV to encode parameters inside request and response data.

## Select VAS

Request data:  
`4f53452e5641532e3031`

Response data (TLV):  
```
6f[1d]:                 # File Control Information Template
  50[08]:               # Application Label   
   4170706c65506179     # ASCII form of "OSE.VAS.01"
  9f21[02]:             # VAS version
   0100                 # Major version 1, minor version 0
  9f24[04]:             # Nonce
   c05d48d0             # This number is random every time
  9f23[04]:             # Extra information
   0000001e             # Meaning of this value is unknown
```

## Get data

Request data (TLV):

**Request data description coming soon ©**

Response data (TLV):
```
70[54]:                 # EMV Proprietary Template
  9f2a[00]              # Unknown
  9f27[4e]:             # Cryptogram Information Data (VAS response)
   beef7375094afa4824addb8abf0a59f4c5b88f7b33cd803666cdf358dc8aa2ec  
   ea863673b7e92b8f39bc744233dda87e53f2ae346eb43415e7b20a50aa41e02d  
   e9f3d533f506e29b4ed31eaa9cfa
```

Cryptogram Information Data TLV tag contains concatenated public key fingerprint and encrypted data that contains the device's timestamp and pass data itself.

**Detailed VAS response breakdown coming soon ©**

# Notes

- This document is based on reverse-engineering efforts done without any access to original protocol specification. Consider all information provided here as an educated guess that is not officially cofirmed;
- If you find any mistakes/typos or have extra information to add, feel free to raise an issue or create a pull request;
- Information provided here is intended for educational and personal purposes only. I assume no responsibility for you using the document for any other purposes. For use in commercial applications you have to contact Apple and pass all required certifications.


# References

* Resources that helped with research:
  - [IOS16 Runtime Headers](https://developer.limneos.net/?ios=16.3);
  - [Apple Developer Documentation](https://developer.apple.com/documentation/);
  - [Contactless passes in Apple Pay](https://support.apple.com/en-gb/guide/security/secbd55491ad/web);
  - [EMV tag search](https://emvlab.org/emvtags/);
  - [Flomio Apple VAS](https://flomio.com/forums/topic/apple-vas/) - VAS available only to licensed partners;
  - [VTAP Apple VAS readers](https://www.vtapnfc.com/apple-vas-readers/) - Use of VAS requires ECP to be implemented in a reader.
  - Device brochures:  
    - [VTAP-100](https://www.vtapnfc.com/downloads/100/VTAP100-OEM_Datasheet.pdf);
    - [VTAP-50](https://www.vtapnfc.com/downloads/50/VTAP50-OEM_Datasheet.pdf);
    - [SpringCard Puck One](https://files.springcard.com/pub/[pfl22016-aa]_puck_one_product_leaflet_EN.pdf);
    - [ACS WalletMate](https://www.acs.com.hk/en/products/548/walletmate-mobile-wallet-nfc-reader-apple-vas-google-smart-tap-certified/);
    - [IDTech PiP](https://idtechproducts.com/datasheets/PiP%20datasheet_v02.22.pdf).
* Devices and software used for analysis:
  - Proxmark3 Easy - used to sniff VAS transactions. Proxmark3 RDV2/4 can also be used;
  - [Proxmark3 Iceman Fork](https://github.com/RfidResearchGroup/proxmark3) - firmware for Proxmark3.