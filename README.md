# Apple VAS


# Overview

Apple VAS (Value-added services) is a proprietary NFC protocol that can be used for sending data from a mobile device to an NFC terminal.

Apart from reading passes, this protocol also allows reader to send a signup URL to the device, causing a signup link notification to appear on devices that do not have an appropriate pass downloaded.

Pass data is transmitted in protected form encrypted using AES-GCM. Shared key is derived via ECDH exchange with a X963KDF and is single use only.

Depending on opreation mode, one or multiple passes can be read in a single tap.  

For correct operation all readers that implement VAS should also have properly configured [ECP](https://github.com/kormax/apple-enhanced-contactless-polling). Otherwise some UX/UI-related features won't work as expected.

Version 1 was current at the time of writing.


# Application identifier


VAS can be selected using following application id (AID):  
   ```
   4f53452e5641532e3031
   ```
AID value is a HEX representation of ASCII string "OSE.VAS.01".  

This AID is also used by [Google Smart Tap](https://github.com/kormax/google-smart-tap):

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
   Value `00`. In this mode the reader works as a signup terminal. Tapping a device to it will display a sign-up notification on the screen.
2. FULL:  
   Value `  01`. Can be used for both pass redemption and URL signup advertisment.

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
   4170706c65506179     # ASCII form of "ApplePay"
  9f21[02]:             # VAS version
   0100                 # Major version 1, minor version 0
  9f24[04]:             # Nonce
   c05d48d0             # This number is random every time
  9f23[04]:             # Extra information
   0000001e             # Meaning of this value is unknown
```

## Get data

### Request data (TLV):

Request data is formed from an array of concatenated TLVs:

| Name                | Tag    | Length   | Example                                                            | Notes                                                                                                                                   |
| ------------------- | ------ | -------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Protocol version    | `9f22` | `02`     | `0100`                                                             | Always `0100`                                                                                                                           |
| SHA256 of pass id   | `9f25` | `32`     | `03b57cdb3eca0984ba9abdc2fb45d86626d87b39d33c5c6dbbc313a6347a3146` | SHA of pass type identifier, such as `pass.com.passkit.pksamples.nfcdemo`                                                               |
| Capabilities mask   | `9f26` | `04`     | `00800002`                                                         | More info below                                                                                                                         |
| Merchant signup URL | `9f29` | Variable | `68747470733a2f2f6170706c652e636f6d`                               | URL pointing to a signup json signed by pass certificate                                                                                |
| Filter              | `9f2b` | `05`     | `0100000000`                                                       | Meaning unknown, mentioned in public configuration PDFs (in References section). Values other than provided in examples make pass reading fail |

### Capabilities mask

Consists of 4 bytes, numbered 0-3 from left to right

Byte 0 - RFU

#### Byte 1:

Mentioned in some public configuration PDFs, does not impact usage

| 07  | 06  | 05  | 04  | 03  | 02  | 01  | 00  | Notes                       |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------- |
| 01  |     |     |     |     |     |     |     | VAS is supported            |
| 00  |     |     |     |     |     |     |     | Vas is unsupported          |
|     | 01  |     |     |     |     |     |     | Authentication required     |
|     | 00  |     |     |     |     |     |     | Authentication not required |
|     |     | XX  | XX  | XX  | XX  |     |     | RFU                         |
|     |     |     |     |     |     | XX  | XX  | Terminal type               |
|     |     |     |     |     |     | 00  | 00  | Payment                     |
|     |     |     |     |     |     | 00  | 01  | Transit                     |


Byte 2 - RFU

#### Byte 3:

Important for protocol operation

| 07  | 06  | 05  | 04  | 03  | 02  | 01  | 00  | Notes                                  |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------------------------------- |
| 00  |     |     |     |     |     |     |     | No passes will be requested after that |
| 01  |     |     |     |     |     |     |     | More passes will be requested later    |
|     | XX  | XX  | XX  | XX  | XX  |     |     | RFU                                    |
|     |     |     |     |     |     | XX  | XX  | VAS mode (like in ECP)                 |
|     |     |     |     |     |     | 00  | 00  | VAS or payment                         |
|     |     |     |     |     |     | 00  | 01  | VAS and payment                        |
|     |     |     |     |     |     | 01  | 00  | VAS only                               |
|     |     |     |     |     |     | 01  | 01  | Payment only                           |


TLV data example:
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

Response data (TLV):
```
70[54]:                 # EMV Proprietary Template
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


Pass public key fingerprint can be calculated by doing a SHA256 over the x component of a public key and taking the first 4 bytes. x is used because for ECDH y value does not matter. For libraries
Fingerprint is used to find the corresponding private key for decryption, as some passes might have a different public key than the others.

Following python pseudocode describes the decryption proccess, crypto methods are provided by [cryptography](https://cryptography.io/en/latest/) library.  As shared info might be considered private information of a company, I won't share how to compute it, but as of now you can find this information on the web, look into notes section for more info. 
```
def decrypt_vas_data(cryptogram: bytearray, pass_identifier: str, keys: Collection[PrivateKey]):
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
                ECSDA_PUBLIC_KEY_ASN_HEADER + bytearray([sign]) + device_public_key_body
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

# Notes

- This document is based on reverse-engineering efforts done without any access to original protocol specification. Consider all information provided here as an educated guess that is not officially cofirmed;
- If you find any mistakes/typos or have extra information to add, feel free to raise an issue or create a pull request;
- Information provided here is intended for educational and personal use only. I assume no responsibility for you using the document for any other purposes. For use in commercial applications you have to contact Apple through official channels and pass all required certifications.
- After the creation of this document a more in-depth reverse-engineered description of Apple VAS has been published by @gm3197. I am in no shape or form affiliated with that person. If you are interested, a full implementation made by that person was added into a Proxmark repository.


# Personal notes

- Even though Apple VAS protocol uses encryption, due to a lack of nonces in data request, makes this protocol unsecure, as an attacker can change the device time and farm pass cryptograms in advance, provided they have an access to device, later using them at an approximate time near a real reader. This could be a reason why express mode is unavailable for passes, as it would make the problem even bigger.
- Due to beforementioned reason we can assume that encryption was also added as a way of preventing the reverse-engineering (which didn't help in the end).


# References

* Resources that helped with research:
  - [IOS16 Runtime Headers](https://developer.limneos.net/?ios=16.3);
  - [Apple Developer Documentation](https://developer.apple.com/documentation/);
  - [Contactless passes in Apple Pay](https://support.apple.com/en-gb/guide/security/secbd55491ad/web) [(Archive)](https://web.archive.org/web/20230126091244/https://support.apple.com/en-gb/guide/security/secbd55491ad/web);
  - [EMV tag search](https://emvlab.org/emvtags/);
  - [Flomio Apple VAS](https://flomio.com/forums/topic/apple-vas/) [(Archive)](https://web.archive.org/web/20230601012002/https://flomio.com/forums/topic/apple-vas/) - VAS available only to licensed partners;
  - [VTAP Apple VAS readers](https://www.vtapnfc.com/apple-vas-readers/) [(Archive)](https://web.archive.org/web/20230401003220/https://www.vtapnfc.com/apple-vas-readers/) - Use of VAS requires ECP to be implemented in a reader.
  - Device Documentation:
    - [Configuring Vendi for Apple VAS](https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Configuring%20Vendi%20for%20AppleVas.pdf?api=v2);
    - [Apple VAS in ViVOPay Devices](https://atlassian.idtechproducts.com/confluence/download/attachments/30479625/Apple%20VAS%20in%20ViVOpay%20Devices%20User%20Guide.pdf?api=v2);
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