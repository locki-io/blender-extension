from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

class NftEnumType(Enum):
    NonFungibleESDT = "NonFungibleESDT"
    SemiFungibleESDT = "SemiFungibleESDT"
    MetaESDT = "MetaESDT"

@dataclass
class ScamInfoType:
    type: str
    info: str

@dataclass
class Owner:
    address: str
    balance: str

@dataclass
class Asset:
    website: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    pngUrl: Optional[str] = None
    svgUrl: Optional[str] = None

@dataclass
class Metadata:
    description: Optional[str] = None
    fileType: Optional[str] = None
    fileUri: Optional[str] = None
    fileName: Optional[str] = None

@dataclass
class Media:
    url: str
    originalUrl: str
    thumbnailUrl: str
    fileType: str
    fileSize: int

@dataclass
class NftType:
    identifier: str
    collection: str
    ticker: Optional[str] = None
    timestamp: int
    attributes: str
    nonce: int
    type: NftEnumType
    name: str
    creator: str
    royalties: int
    balance: str
    uris: Optional[List[str]] = field(default_factory=list)
    url: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)
    decimals: Optional[int] = None
    owner: Optional[str] = None
    supply: Optional[str] = None
    isWhitelistedStorage: Optional[bool] = None
    owners: Optional[List[Owner]] = field(default_factory=list)
    assets: Optional[Asset] = None
    metadata: Optional[Metadata] = None
    media: Optional[List[Media]] = field(default_factory=list)
    scamInfo: Optional[ScamInfoType] = None
