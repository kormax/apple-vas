# Apple VAS


# Overview

Apple VAS (Value-added services) is a proprietary NFC protocol that can be used for sending data from a mobile device to an NFC terminal.

Apart from reading passes, this protocol also allows reader to send a signup URL to the device, causing a signup link notification to appear on devices that do not have an appropriate pass downloaded.

Pass data is transmitted in protected form encrypted using AES-GCM. Shared key is derived via ECDH exchange with a X963KDF and is single use only.

Depending on opreation mode, one or multiple passes can be read in a single tap.  

For correct operation all readers that implement VAS should also have properly configured [ECP](https://github.com/kormax/apple-enhanced-contactless-polling). Otherwise some UX/UI-related features won't work as expected. Following information assumes that it is used.

Version 1 was current at the time of writing.


# Application identifier


VAS can be selected using following application id (AID):  
   ```
   4f53452e5641532e3031
   ```
AID value is a HEX representation of ASCII string "OSE.VAS.01".  

This AID is also used by [Google Smart Tap](https://github.com/kormax/google-smart-tap):

The ususal implementation for most readers is to select OSE.VAS.01 in order to detect what wallet provider is available on device (stored in TLV tag `50`), if "ApplePay" is the value, then we have a device with Apple Wallet.


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

# Command overview

As of version 1 following commands are available:

| Command name | CLA | INS | P1  | P2   | DATA    | LE  | Notes                       |
| ------------ | --- | --- | --- | ---- | ------- | --- | --------------------------- |
| Select VAS   | 00  | A4  | 04  | 00   | VAS AID | 00  |                             |
| Get data     | 80  | CA  | 01  | MODE | *       | 00  | Data format described below |


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



<sub>[ and ] depict inclusive array indices, ( and ) depict exclusive indices</sub>


Cryptogram Information Data TLV tag contains following concatenated data:
   - Pass public key fingerprint: [0:4) (4 bytes);
   - Device public key: [4:36) (32 bytes);
   - Encrypted data [36:] containing:
     * Device timestamp [0:4) (4 bytes);
     * Pass data [4:] (n bytes).

# Decryption

Before you can decrypt the pass data, you have to get the private key that matches the public key of the pass, as it is possible that the keys are rolled over from time to time, or that they are semi-diversified. Finding the private key can be done with pass public key fingerprint data.  
Pass public key fingerprint can be calculated by doing a SHA256 over the X component of a public key and taking the first 4 bytes. Only X component is used because for ECDH Y value does not matter. If your library requires it, you can prepend any sign byte (`02`, `03`) to the EC public key data.

After finding the matching private key, you have to extract the session key provided by the device, and perform an ECDH exchange, retreiving the common key.

Common key itself is not used as is, instead another key has to be derived from it using the X963KDF via SHA256. One culprit that hindered the reverse-engineering efforts of this protocol was the shared info that was needed in order to properly derive the encryption key. As am hesitant to publish the deriviation info, I won't share it. But great news is that as of now this information [has been published](https://gist.github.com/gm3197/ad0959476346cef69b75ea0523214350), you can look at the document for more info.  

Following python pseudocode describes the decryption proccess, crypto methods are provided by [cryptography](https://cryptography.io/en/latest/) library, correct shared info calculation is omitted (refer to link for info).
```
import hashlib 

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_der_public_key

PUBLIC_KEY_ASN_HEADER = bytearray.fromhex(
   "3039301306072a8648ce3d020106082a8648ce3d030107032200"
)

def generate_shared_info(pass_identifier: str):
    return bytes([
        *"ASN 1 RELATIVE-OID".encode("ascii"),
        *"REDACTED REDACTED REDACTED".encode("ascii"),
        *hashlib.sha256(pass_identifier.encode("ascii")).digest()
    ])

def decrypt_vas_data(cryptogram: bytearray, pass_identifier: str, keys: Collection["PrivateKey"]):
   device_key_id = cryptogram[:4]
   device_public_key_body = cryptogram[4: 32 + 4]
   device_encrypted_data = cryptogram[36:]

   for key in keys:
      reader_public_key = key.public_key()
      reader_key_id = bytearray(hashlib.sha256(reader_public_key.public_numbers().x.to_bytes(32, "big")).digest()[:4])
      if reader_key_id == device_key_id:
         reader_private_key = key
         break
   else:
      raise Exception("No matching private key was found for this pass")

   # Sign does not matter for ECDH
   for sign in (0x02, 0x03):
      try:
         device_public_key = load_der_public_key(
               PUBLIC_KEY_ASN_HEADER + bytearray([sign]) + device_public_key_body
         )

         shared_key = reader_private_key.exchange(ec.ECDH(), device_public_key)
         shared_info = generate_shared_info(pass_identifier)
         print(f"SHARED INFO {shared_info.hex()} {len(shared_info)}")
         derived_key = X963KDF(
               algorithm=hashes.SHA256(),
               length=32,
               sharedinfo=shared_info,
         ).derive(shared_key)

         device_data = AESGCM(derived_key).decrypt(b'\x00' * 16, bytes(device_encrypted_data), b'')

         timestamp = datetime(year=2001, month=1, day=1) + timedelta(seconds=int.from_bytes(device_data[:4], "big"))
         payload = device_data[4:].decode("utf-8")
         print(f"{timestamp} {payload}")
         return timestamp, payload
      except Exception as e:
         pass
   else:
      raise Exception("Could not decrypt data")
```

# Communication example

Reading single pass

```
Select VAS applet:
    --> ISO7816Command(cla=0x00; ins=0xa4; p1=0x04; p2=0x00; lc=10; data=4f53452e5641532e3031; le=0)
    <-- ISO7816Response(sw1=0x90; sw2=0x00; data=6f1d50084170706c655061799f210201009f2404e9caede39f23040000003e(31))
        Data TLV:
            6f[1d]:
               50[08]: 
                  4170706c65506179
               9f21[02]: 
                  0100
               9f24[04]: 
                  e9caede3
               9f23[04]: 
                  0000003e

Get VAS data:
    --> ISO7816Command(cla=0x80; ins=0xca; p1=0x01; p2=0x01; lc=75; data=9f220201009f252003b57cdb3eca0984ba9abdc2fb45d86626d87b39d33c5c6dbbc313a6347a31469f2604008000029f2b0501000000009f291168747470733a2f2f6170706c652e636f6d; le=0)
        Data TLV:
            9f22[02]: 
               0100
            9f25[20]: 
               03b57cdb3eca0984ba9abdc2fb45d86626d87b39d33c5c6dbbc313a6347a3146
            9f26[04]: 
               00800002
            9f2b[05]: 
               0100000000
            9f29[11]: 
               68747470733a2f2f6170706c652e636f6d
    <-- ISO7816Response(sw1=0x90; sw2=0x00; data=70549f2a009f274ec0b77375d3f37956d84a538f28ac2a04b38ddc1a67d3647a4dd30abd736ea1cea8038388692e89db99e4746d872de782395640c536e79a75c47a9343da0af3937f06eeca7a865c4ad05a2c543ad2(86))
        Data TLV:
            70[54]:
               9f2a[00]
               9f27[4e]: 
                  c0b77375d3f37956d84a538f28ac2a04b38ddc1a67d3647a4dd30abd736ea1cea8038388692e89db99e4746d872de782395640c536e79a75c47a9343da0af3937f06eeca7a865c4ad05a2c543ad2

Decrypting VAS data:
   device_key_id = cryptogram[:4] = c0b77375
   device_public_key_body = cryptogram[4: 32 + 4] = d3f37956d84a538f28ac2a04b38ddc1a67d3647a4dd30abd736ea1cea8038388
   device_encrypted_data = cryptogram[36:] = 692e89db99e4746d872de782395640c536e79a75c47a9343da0af3937f06eeca7a865c4ad05a2c543ad2

   timestamp = device_data[:4] = 2023-07-09 16:35:58
   payload = device_data[4:] = 6d1UlFpnOc50iVKRaboDOK

VAS result is AppleVasResult(passes=[Pass(identifier=pass.com.passkit.pksamples.nfcdemo; key_id=c0b77375; timestamp=2023-07-09 16:35:58; value=6d1UlFpnOc50iVKRaboDOK)])
```


# Notes

- This document is based on reverse-engineering efforts done without any access to original protocol specification. Consider all information provided here as an educated guess that is not officially cofirmed;
- If you find any mistakes/typos or have extra information to add, feel free to raise an issue or create a pull request;
- Information provided here is intended for educational and personal use only. I assume no responsibility for you using the document for any other purposes. For use in commercial applications you have to contact Apple through official channels and pass all required certifications.
- After the creation of this document a more in-depth reverse-engineered description of Apple VAS [has been published](https://gist.github.com/gm3197/ad0959476346cef69b75ea0523214350) by [@gm3197](https://github.com/gm3197). I am in no shape or form affiliated with that person. If you are interested, you can look at their GitHub profile, plus there is a fully complete implementation made by that person was added into a [Proxmark3](https://github.com/RfidResearchGroup/proxmark3) repository. This repository will still be maintained as some information here is unique, plus updates may be in order if new information is found.


# Personal notes

- Protocol lacks nonces, therefore there is no way for a reader to truly verify that the response provided was actually generated during this communication session.  
  An attacker, provided that they have temporary access to victim's device, can farm cryptograms in advance after changing devie time to a particular date. After that, they can use farmed cryptograms at a right moment. 
- Timestamp-based verification is a tale about compromises. You can reduce allowed timestamp diff between a reader and phone, but this could cause false negatives.
  On the other hand, making a diff larger or non-existant makes the possible attack easier. There is a big chance that some real certified readers don't verify the timestamp at all to reduce false positives;
- Google Smart Tap seems to have better security. It uses a static key for reader authentication, a secure channel is established afterwards using a per-session unique ECDH keys, plus the request is nonced.
- One could argue that physical access to device is a game over anyway, as you can extract a pass file or even share it, so security might not have been a first priority.
- Due to beforementioned reasons we can assume that encryption was also added as a way of preventing the reverse-engineering and/or as an afterthought (which didn't help in the end).


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