# Apple VAS

Apple VAS (Value-added services) is a proprietary NFC protocol that can be used for sending data from a mobile device to an NFC terminal.

This protocol also has a secondary feature that allows reader to send a signup URL to the device, causing a signup link notification to appear on devices that do not have an appropriate pass in store.

Pass data is transmitted in encrypted form. Shared key is derived via ECDH exchange and is single use only.

Depending on the VAS mode, one or multiple passes can be read in a single tap.

Version 1 was current at the time of writing.


# Application identifiers


VAS can be activated using following application id (AID):

1. VAS AID (hex of encoded 'OSE.VAS.01'), also used by Google Smart Tap.  
    ```
    4f53452e5641532e3031
    ```

The ususal implementation for most readers is to select OSE.VAS.01 in order to detect what wallet provider is available on device (stored in TLV tag 50), if "ApplePay" is the value, then we have a device with Apple Wallet.


# Modes

Apple VAS has multiple operation modes, mode setting affects how the system UI will react to the transaction.

1. VAS or payment:  
   Operates the same as VAS and payment (Info below). Can also be called VAS over payment, meaning that a reader tries to read a loyalty pass, if it has enough balance it ends the transaction.  Otherwise it tries to charge the selected payment card.
2. VAS and payment:  
   Also called single tap mode. In this mode reader should select a VAS applet, read loyatly info, and after that select a payment applet and finish a transaction. **This mode supports reading multiple different passes in a single tap**, although UI will only tell about the first one. In this mode bringing the device to the field will display a default payment card, after auth it will also display that "Pass X will be also used" under the card.  
   <img src="./assets/VAS.MODE.VASANDPAY.webp" alt="![VAS and payment]" width=200px>
3. VAS only:  
   Used when you only need to read a pass. In this mode if a phone is brought into the field before auth it will present the needed pass on the screen for authentication. **This mode allows to read only one pass at a time**. If you preauthenticate a payment card, a needed pass will jump in place of a payment card when you bring the device to the reader.  
   <img src="./assets/VAS.MODE.VASONLY.BEFORE.AUTH.webp" alt="![VAS and payment]" width=200px>
4. Payment only:
   Serves as anti-CATHAY. Also needed for URL signup.


VAS also has a protocol mode flag, which defines following two protocol modes (although in practice it makes no difference in operation):
1. URL:  
   In this mode the reader works as a signup terminal. Tapping a device to it will display a sign-up notification on the screen.
2. FULL:  
   Can be used for both pass redemption and signup advertisment.


# Commands


As of version 1 following commands are available:

| Command name             | CLA  | INS  | P1   | P2   | DATA             | LE   | NOTES                                       |
|--------------------------|------|------|------|------|------------------|------|---------------------------------------------|
| Select VAS               | 00   | A4   | 04   | 00   | VAS AID          | 00   |                                             |
| Get data                 | 80   | CA   | 01   | MODE | SOON             | 00   |                                             |


VAS uses TLV to encode parameters in data payloads. Some parameters are optional. 


