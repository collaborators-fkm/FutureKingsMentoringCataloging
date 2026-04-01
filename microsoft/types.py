from typing import Any, NotRequired, TypedDict


type GraphHeaders = dict[str, str]


class GraphUser(TypedDict, total=False):
    email: str
    displayName: str


class GraphIdentity(TypedDict, total=False):
    user: GraphUser


class GraphParentReference(TypedDict, total=False):
    driveType: str
    driveId: str
    id: str
    name: str
    path: str
    siteId: str


class GraphHashes(TypedDict, total=False):
    quickXorHash: str


class GraphFileFacet(TypedDict, total=False):
    fileExtension: str
    hashes: GraphHashes
    mimeType: str


class GraphFileSystemInfo(TypedDict, total=False):
    createdDateTime: str
    lastModifiedDateTime: str


class GraphShared(TypedDict, total=False):
    scope: str


class GraphFolderFacet(TypedDict, total=False):
    childCount: int


class GraphDriveItem(TypedDict, total=False):
    id: str
    name: str
    size: int
    createdDateTime: str
    lastModifiedDateTime: str
    webUrl: str
    eTag: str
    cTag: str
    createdBy: GraphIdentity
    lastModifiedBy: GraphIdentity
    parentReference: GraphParentReference
    file: NotRequired[GraphFileFacet]
    fileSystemInfo: NotRequired[GraphFileSystemInfo]
    shared: NotRequired[GraphShared]
    folder: NotRequired[GraphFolderFacet]
    odata_context: NotRequired[str]
    download_url: NotRequired[str]
    additional_data: NotRequired[dict[str, Any]]
