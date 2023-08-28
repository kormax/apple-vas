# Apple VAS


# Overview

Apple VAS (Value-added services) is a proprietary NFC protocol that can be used for sending data from a mobile device to an NFC terminal.

Apart from reading passes, this protocol also allows reader to send a signup URL to the device, causing a signup link notification to appear on devices that do not have an appropriate pass downloaded.

Pass data is transmitted in protected form encrypted using AES-GCM. Shared key is derived via ECDH exchange with a X963KDF and is single use only.

Depending on opreation mode, one or multiple passes can be read in a single tap.  

Version 1 was current at the time of writing.


# Application identifier


VAS can be selected using following application id (AID):  
   ```
   4f53452e5641532e3031
   ```
AID value is a HEX representation of ASCII string `OSE.VAS.01`.  

This AID is also used by [Google Smart Tap](https://github.com/kormax/google-smart-tap):

The ususal implementation for most readers is to select `OSE.VAS.01` in order to detect what wallet provider is available on device (stored in TLV tag `50`), if `ApplePay` is the value, then we have a device with Apple Wallet.


# Modes

## Operation modes

Apple VAS has multiple operation modes. Mode setting affects:
* How the system UI will react to the transaction.
* If you are allowed to read multiple different passes in one tap.
  
Following modes are available:
1. VAS or payment `00`:  
   Operates the same as VAS and payment (Info below). Can also be called VAS over payment, meaning that a reader tries to read a loyalty pass, if it has enough balance it ends the transaction.  Otherwise it tries to charge the selected payment card.
2. VAS and payment `01`:  
   Also called single tap mode. In this mode reader should select a VAS applet, read loyatly info, and after that select a payment applet and finish a transaction. **This mode supports reading multiple different passes in a single tap**, although UI will only tell about the first one. In this mode bringing the device to the field will display a default payment card, after auth it will also display that "Pass X will be also used" under the card.  
   <img src="./assets/VAS.MODE.VASANDPAY.webp" alt="![VAS and payment]" width=200px>
3. VAS only `02`:  
   Used when you only need to read a pass. In this mode if a phone is brought into the field before auth it will present the needed pass on the screen for authentication. **This mode allows to read only one pass at a time**. If you preauthenticate a payment card, a needed pass will jump in place of a payment card when you bring the device to the reader.  
   <img src="./assets/VAS.MODE.VASONLY.BEFORE.AUTH.webp" alt="![VAS and payment]" width=200px>
4. Payment only `03`:  
   Forces a payment card to appear on a screen for authentication (like any other regular NFC field), but also serves as anti-CATHAY. 

## Protocol modes

VAS also has a protocol MODE flag.

1. URL:  
   Value `00`. In this mode the reader works as a signup terminal. Tapping a device to it will display a sign-up notification on the screen.
2. FULL:  
   Value `01`. Can be used for both pass redemption and URL signup advertisment.


# ECP

For correct operation all readers that implement VAS have to have properly configured [ECP](https://github.com/kormax/apple-enhanced-contactless-polling).  
Otherwise some UX/UI-related features:
- Won't work as expected: 
  * "Pass will be used" tooltip under a payment card when device is brought to the reader in VAS and/or Payment operation mode.
- Won't work at all:
  * Pass suggestions when device is brought to the reader in VAS ONLY operation mode.

VAS ECP frames are also sometimes referred to as VASUP-A, both refer to the same thing.

All known VAS frames use ECP format V1, and they differ in last byte only, depending on operation mode: 

| Name            | Version | TCI      |
| --------------- | ------- | -------- |
| VAS or payment  | 01      | 00 00 00 |
| VAS and payment | 01      | 00 00 01 |
| VAS only        | 01      | 00 00 02 |
| Payment only    | 01      | 00 00 03 |

Payment only configuration might seem rudimentary, as phone reacts to any reader as to payment one by displaying a payment card.  
But it is not the case if a [chinese transit card is added to device](https://github.com/kormax/apple-device-as-access-card), which this configuration helps with.

# Command overview

As of version 1 following commands are available:

| Command name      | CLA | INS | P1  | P2   | DATA    | LE  | RESPONSE DATA | Notes                       |
| ----------------- | --- | --- | --- | ---- | ------- | --- | ------------- | --------------------------- |
| SELECT VAS APPLET | 00  | A4  | 04  | 00   | VAS AID | 00  | BER-TLV       |                             |
| GET DATA          | 80  | CA  | 01  | MODE | BER-TLV | 00  | BER-TLV       | Data format described below |

Commands are executed as follows:
1. SELECT VAS APPLET:  
   Reader transmits universal VAS AID; Device response with wallet implementation name in TLV tag `50`.  
   If value is `4170706c65506179`, which is a value of `ApplePay` string in ASCII-encoded form, we have a device that supports Apple VAS.  
   Other than that, device return current implementation version, a nonce (which is unused), and extra information.  
2. GET DATA:  
   Reader sends protocol mode flag, selected protocol version, SHA256 of pass identifier, capabilities mask, and optional signup URL and filter values.  
   Device responds with encrypted pass data or an error code in FULL VAS protocol mode, and a confirmation in URL ONLY protocol mode.  
   In VAS And/Or Payment operation mode, reader may send this command multiple times during the same session in order to get passes from different providers. 
   In VAS only operation mode, this command is executed only one time.  
*  After a reading session has been completed, reader should DESELECT the device and do a TRESET to signify end of the transaction.  
   It is required because VAS supports operation in combination with payment cards that are implemented using other NFC modes, for instance, Type F (FeliCa).  
   DESELECT + TRESET in this case tells a device that it can now update NFC controller routing and configuration to match the configuration of a pending payment pass.  
   Beware that due to that reason in `VAS and/or payment` modes, if you've failed to a read a pass due to connectivity issue, you shouldn't do a DESELECT and TRESET, as after that a device won't route any more requests to VAS until user preemptively ends and re-authenticates the session. 


# Command and response data format

## Select VAS

### Request:

   | CLA | INS | P1  | P2  | DATA                   | LE  | 
   | --- | --- | --- | --- | ---------------------- | --- |
   | 00  | A4  | 04  | 00  | `4f53452e5641532e3031` | 00  | 

   Data contains an ASCII encoded form of "OSE.VAS.01" string;

### Response
   
   | SW1 | SW2 | DATA                                                             |
   | --- | --- | ---------------------------------------------------------------- |
   | 90  | 00  | `6f1d50084170706c655061799f210201009f2404c05d48d09f23040000001e` |


   Response data example:  
   - Payload:
     - `6f1d50084170706c655061799f210201009f2404c05d48d09f23040000001e`
   - TLV decoded:
      ```
      6f[1d]:                 # File Control Information Template
         50[08]:               # Application Label   
            4170706c65506179     # ASCII form of "ApplePay"
         9f21[02]:             # VAS version
            0100                 # Major version 1, minor version 0
         9f24[04]:             # Nonce
            c05d48d0             # This number is random every time, not used
         9f23[04]:             # Extra information
            0000001e             # Meaning of this value is unknown
      ```


## Get data

### Request:

   | CLA | INS | P1  | P2   | DATA | LE  |
   | --- | --- | --- | ---- | ---- | --- |
   | 80  | CA  | 01  | MODE | *    | 00  |

   P2 flag values were described in "Protocol Modes" section;

   Request data:
   | Name                | Tag    | Length   | Example                                                            | Notes                                                                                                                                              |
   | ------------------- | ------ | -------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
   | Protocol version    | `9f22` | `02`     | `0100`                                                             | Always `0100`                                                                                                                                      |
   | SHA256 of pass id   | `9f25` | `32`     | `03b57cdb3eca0984ba9abdc2fb45d86626d87b39d33c5c6dbbc313a6347a3146` | SHA of pass type identifier, such as `pass.com.passkit.pksamples.nfcdemo`                                                                          |
   | Capabilities mask   | `9f26` | `04`     | `00800002`                                                         | More info below                                                                                                                                    |
   | Merchant signup URL | `9f29` | Variable | `68747470733a2f2f6170706c652e636f6d`                               | URL pointing to a HTTPS signup json signed by pass certificate                                                                                     |
   | Filter              | `9f2b` | `05`     | `0100000000`                                                       | Meaning unknown, mentioned in public configuration PDFs (look at References section). Values other than provided in example make pass reading fail |

### Capabilities mask

Consists of 4 bytes, numbered 0-3 from left to right

Byte 0 - RFU

#### Byte 1:

Mentioned in some public configuration PDFs, does not impact usage

| 07  | 06  | 05  | 04  | 03  | 02  | 01  | 00  | Notes                       |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------- |
| 1   |     |     |     |     |     |     |     | VAS is supported            |
| 0   |     |     |     |     |     |     |     | Vas is unsupported          |
|     | 1   |     |     |     |     |     |     | Authentication required     |
|     | 0   |     |     |     |     |     |     | Authentication not required |
|     |     | X   | X   | X   | X   |     |     | RFU                         |
|     |     |     |     |     |     | X   | X   | Terminal type               |
|     |     |     |     |     |     | 0   | 0   | Payment                     |
|     |     |     |     |     |     | 0   | 1   | Transit                     |


Byte 2 - RFU

#### Byte 3:

Important for protocol operation

| 07  | 06  | 05  | 04  | 03  | 02  | 01  | 00  | Notes                                                    |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------------------------------------------------- |
| 1   |     |     |     |     |     |     |     | More passes will be requested in this reading session    |
| 0   |     |     |     |     |     |     |     | No more passes will be requested in this reading session |
|     | X   | X   | X   | X   | X   |     |     | RFU                                                      |
|     |     |     |     |     |     | X   | X   | VAS mode (like in ECP)                                   |
|     |     |     |     |     |     | 0   | 0   | VAS or payment                                           |
|     |     |     |     |     |     | 0   | 1   | VAS and payment                                          |
|     |     |     |     |     |     | 1   | 0   | VAS only                                                 |
|     |     |     |     |     |     | 1   | 1   | Payment only                                             |


Command TLV data example:
   - TLV decoded: 
      ```
      9f22[02]:
      0100
      9f25[20]:             
         03b57cdb3eca
         0984ba9abdc2
         fb45d86626d8
         7b39d33c5c6d
         bbc313a6347a
         3146
      9f26[04]:
         00800002
      9f2b[05]:
         0100000000
      9f29[11]:               
         68747470733a2f2f6170706c652e636f6d
      ```


### Response:

   | SW1 | SW2 | DATA                                                                                                                                                                           |
   | --- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
   | XX  | XX  | `70549f2a009f274ebeef7375094afa4824addb8abf0a59f4c5b88f7b33cd803666cdf358dc8aa2ecea863673b7e92b8f39bc744233dda87e53f2ae346eb43415e7b20a50aa41e02de9f3d533f506e29b4ed31eaa9cfa` |

Status words:
   | SW1  | SW2  | Notes                                                                                         |
   | ---- | ---- | --------------------------------------------------------------------------------------------- |
   | `90` | `00` | Pass data returned (full VAS) or URL was accepted (URL only)                                  |
   | `6a` | `83` | Pass not selected on a screen or unavailable                                                  |
   | `62` | `87` | Device not unlocked (Apple Wallet will open, pass will appear on a screen for authentication) |

Any other status word means that a command payload was built incorrectly, or that an applet was not yet selected.

Response data example:
   - Payload:
     - `70549f2a009f274ebeef7375094afa4824addb8abf0a59f4c5b88f7b33cd803666cdf358dc8aa2ecea863673b7e92b8f39bc744233dda87e53f2ae346eb43415e7b20a50aa41e02de9f3d533f506e29b4ed31eaa9cfa`
   - TLV decoded: 
      ```
      70[54]:               # EMV Proprietary Template
         9f2a[00]              # Unknown
         9f27[4e]:             # Cryptogram Information Data (VAS response)
            beef7375094afa4824addb8abf0a59f4c5b88f7b33cd803666cdf358dc8aa2ec  
            ea863673b7e92b8f39bc744233dda87e53f2ae346eb43415e7b20a50aa41e02d  
            e9f3d533f506e29b4ed31eaa9cfa
      ```

<sub>Symbols [ and ] depict inclusive array indices, ( and ) depict exclusive indices. Numeration is done simillarly to Python</sub>


Cryptogram Information Data TLV tag contains following concatenated data:
   - Pass public key fingerprint: [0:4) (4 bytes);
   - Device public key: [4:36) (32 bytes);
   - Encrypted data [36:] containing:
     * Device timestamp [0:4) (4 bytes);
     * Pass data [4:] (n bytes).

# Decryption

After receiving the response, the next step is to decrypt it.

Due to a nature of Apple VAS protocol, decryption can be done:
- Online, in real-time directly on the reader or connected device:  
  * Suits most cases, with the only disadvantage that decryption keys need to be distributed onto many devices.
- Offline, with cryptogram/transaction data and ephemeral keys uploaded to the remote server/machine containing needed keys:  
  * Advantage of offline method is that there is no need to distribute the decryption keys, so you keep your data a bit more secure.  
  * It suits implementations where points are not subtracted but only added (like after a purchase), etc.


In both situations, decryption is done in the following steps:
1. First 4 bytes of cryptogram data are taken, it's the key identifier of the pass public key `key_identifier`.  
   Key identifier is important, as depending on backend implementation, pass keys may be rolled over over time, or be diversified between pass batches.  
   Even in single key situations, it can be used in order to verify that you're attempting to decrypt a correct pass and not something else.
2. Using the key identifier, we find matching pass private key by iterating through a list of private keys (better cache them, example only).
   1. Derive public key based on private key;
   2. Get public key bytes of the X component.  
      Only X component is used because for ECDH Y value does not matter.  
      If your library requires it, you can prepend any sign byte (`02`, `03`) to the EC public key data if you want to load it into an object representation;
   3. Calculate key identifier by doing SHA256 over the X component. Take first 4 bytes;
   4. Compare if instance key identifier matches the pass key identifier. If it's a match, then we have the corresponding private key.
3. Using the pass private key, do ECDH exchange with device ephemeral key, receiving shared key `shared_key`;
4. Shared key `shared_key` is used together with shared info `shared_info` in X963KDF algorithm in order to get the derived key `derived_key`;
5. Derived key `derived_key` is then used via AESGCM in order to decrypt pass data.

Documentation on how to generate shared information and derived keys (steps 4. 5.) is not present in this document.
For that information, visit [the following gist](https://gist.github.com/gm3197/ad0959476346cef69b75ea0523214350).  Don't forget to thank the authour. 

File located at [examples/implementation/decryption.py](./examples/implementations/decryption.py) contains Python code that implements the decryption proccess.  
Crypto methods are provided by [cryptography](https://cryptography.io/en/latest/) library.  
Correct shared info calculation is omitted, but can be reconstructed by following the link mentioned in this section before.

# Notes

- For communication traces and decryption example code, visit the [Examples](./examples/README.md) directory.
- If you find any mistakes/typos or have extra information to add, feel free to raise an issue or create a pull request;
- This document is based on reverse-engineering efforts done without any access to original protocol specification.  
  Take all information provided here with a grain of salt. Understand that it does not and won't have any official confirmation and may or may not contain mistakes;
- Information provided in this repository is intended for educational, research, and personal use. Its use in any other way is not encouraged.  
- **Beware** that Apple VAS, just like any other proprietary technology, might be a subject to legal protections depending on jurisdiction. A mere fact of it being reverse-engineered **does not** always mean that it can be used in a commercial product as-is without causing an infringement.  
  For use in commercial applications, you should contact Apple through official channels in order to get approval.
- After initial material for this repository has been added and slowly expanded upon with infrequent updates, a fully complete reverse-engineered description of Apple VAS [has been published](https://gist.github.com/gm3197/ad0959476346cef69b75ea0523214350) by [@gm3197](https://github.com/gm3197).  
  I am in no way, shape or form affiliated with that person. All findings described here were made on my own.  
  Nevertheless, considering the timings, **they were the first one** to publish the **fully reproducible Apple VAS spec**, so **much gratitude** should be dedicated **to them** in this regard.  
  To support their work, give their repo/profile a visit/bookmark, you'd need to do that anyway in order to get information on shared info generation :).
- If you are interested in a fully code-complete Apple VAS implementation, you can look at the one made by [@gm3197](https://github.com/gm3197) that was added into a [Proxmark3](https://github.com/RfidResearchGroup/proxmark3) repository. Look for it via `VAS`, `vas` keywords. 

# Personal notes

- Protocol lacks nonces, therefore there is no way for a reader to truly verify that the response provided was actually generated during this communication session.  
  An attacker, provided that they have temporary access to victim's device, can farm cryptograms in advance after changing devie time to a particular date. After that, they can use farmed cryptograms at a right moment. 
- Timestamp-based verification is a tale about compromises. You can reduce allowed timestamp diff between a reader and phone, but this could cause false negatives.
  On the other hand, making a diff larger or non-existant makes the possible attack easier. There is a big chance that some real certified readers don't verify the timestamp at all to reduce false positives;
- Google Smart Tap seems to have better security. It uses a static key for reader authentication, a secure channel is established afterwards using a per-session unique ECDH keys, plus the request is nonced.
- One could argue that physical access to device is a game over anyway, as you can extract a pass file or even share it, so security might not have been a first priority.
- Due to beforementioned reasons we can assume that encryption was also added as a way of preventing the reverse-engineering and/or as an afterthought (which didn't help in the end).
- Protocol has some loose ends, such as filters, nonces, feature flags. It could be a sign of data yet to uncover, or a memento of long forgotten plans to update the protocol. If anything on that matter comes by, this repository will be updated.
 
# References

* Resources that helped with research:
  - Generating Wallet passes for testing and analysis:
    - [PassKit](https://pub1.pskt.io/c/gn1v07) - the easiest way of getting demo passes for both Apple VAS and Google Smart Tap, to get an Apple Wallet pass you have to open this link with an Apple-related (IOS/Mac) user agent;
    - [SpringCard](https://springpass.springcard.com) - requires email, can be used for extra testing;
  - General:
    - [IOS16 Runtime Headers](https://developer.limneos.net/?ios=16.3);
    - [EMV tag search](https://emvlab.org/emvtags/);
  - Apple resources:
    - [Apple Developer Documentation](https://developer.apple.com/documentation/);
    - [Contactless passes in Apple Pay](https://support.apple.com/en-gb/guide/security/secbd55491ad/web) [(Archive)](https://web.archive.org/web/20230126091244/https://support.apple.com/en-gb/guide/security/secbd55491ad/web);
  - ECP Requirement info:
    - [Flomio Apple VAS](https://flomio.com/forums/topic/apple-vas/) [(Archive)](https://web.archive.org/web/20230601012002/https://flomio.com/forums/topic/apple-vas/) - VAS available only to licensed partners;
    - [VTAP Apple VAS readers](https://www.vtapnfc.com/apple-vas-readers/) [(Archive)](https://web.archive.org/web/20230401003220/https://www.vtapnfc.com/apple-vas-readers/) - Use of VAS requires ECP to be implemented in a reader.
  - Device documentation:
    - [Springcard - Apple VAS Template](https://docs.springcard.com/books/SpringCore/Smart_Reader_Operation/NFC_Templates/Apple_VAS) [(Archive)](https://web.archive.org/web/20230709162304/https://docs.springcard.com/books/SpringCore/Smart_Reader_Operation/NFC_Templates/Apple_VAS);
    - [Configuring Vendi for Apple VAS](https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Configuring%20Vendi%20for%20AppleVas.pdf?api=v2) [(Archive)](https://web.archive.org/web/20230709161922/https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Configuring%20Vendi%20for%20AppleVas.pdf?api=v2);
    - [Apple VAS in ViVOPay Devices](https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Apple%20VAS%20in%20ViVOpay%20Devices%20User%20Guide.pdf?api=v2) [(Archive)](https://web.archive.org/web/20230630105151/https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Apple%20VAS%20in%20ViVOpay%20Devices%20User%20Guide.pdf?api=v2);
    - [Socket Mobile](https://www.socketmobile.com/support/data-editing-barcode/enable-disable-data/nfc/apple-value-added-services);
  - Device brochures:  
    - [VTAP-100](https://www.vtapnfc.com/downloads/100/VTAP100-OEM_Datasheet.pdf);
    - [VTAP-50](https://www.vtapnfc.com/downloads/50/VTAP50-OEM_Datasheet.pdf);
    - [SpringCard Puck One](https://files.springcard.com/pub/[pfl22016-aa]_puck_one_product_leaflet_EN.pdf);
    - [ACS WalletMate](https://www.acs.com.hk/en/products/548/walletmate-mobile-wallet-nfc-reader-apple-vas-google-smart-tap-certified/);
    - [IDTech PiP](https://idtechproducts.com/datasheets/PiP%20datasheet_v02.22.pdf).
* Devices and software used for analysis:
  - Proxmark3 Easy - used to sniff VAS transactions. Proxmark3 RDV2/4 can also be used;
  - [Proxmark3 Iceman Fork](https://github.com/RfidResearchGroup/proxmark3) - firmware for Proxmark3;
  - [Python cryptography library](https://cryptography.io/en/latest/).
