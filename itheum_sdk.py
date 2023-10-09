from dataclasses import dataclass
import base64

from . import abiRegistry
from . import BinaryCodec

@dataclass
class NftType:
    attributes: str
    identifier: str
    url: str
    name: str
    supply: int
    royalties: float
    nonce: int
    collection: str

@dataclass
class DataNftMetadataType:
    index: int
    id: str
    nftImgUrl: str
    dataPreview: str
    dataStream: str
    dataMarshal: str
    tokenName: str
    creator: str
    creationTime: int  # You might change this to datetime.datetime based on your requirements
    supply: int
    description: str
    title: str
    royalties: float
    nonce: int
    collection: str
    balance: int

def decode_nft_attributes(nft: NftType, index: int = 0) -> DataNftMetadataType:
    # placeholder for abiRegistry.getStruct() equivalent
    data_nft_attributes = abiRegistry.getStruct("DataNftAttributes")

    # placeholder for new BinaryCodec().decodeTopLevel() equivalent
    decoded_attributes = BinaryCodec().decode_top_level(base64.b64decode(nft.attributes), data_nft_attributes).value_of()

    data_nft = DataNftMetadataType(
        index=index,
        id=nft.identifier,
        nftImgUrl=nft.url,
        dataPreview=str(decoded_attributes["data_preview_url"]),
        dataStream=str(decoded_attributes["data_stream_url"]),
        dataMarshal=str(decoded_attributes["data_marshal_url"]),
        tokenName=nft.name,
        creator=str(decoded_attributes["creator"]),
        creationTime=int(decoded_attributes["creation_time"]) * 1000,  # You might use datetime.datetime.fromtimestamp here
        supply=nft.supply if nft.supply else 0,
        description=str(decoded_attributes["description"]),
        title=str(decoded_attributes["title"]),
        royalties=nft.royalties / 100 if nft.royalties else 0,
        nonce=nft.nonce,
        collection=nft.collection,
        balance=0
    )

    return data_nft
