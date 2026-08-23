using Newtonsoft.Json;
using System;

namespace Nebula.Net
{
    [Serializable]
    public class InventoryItemDto
    {
        [JsonProperty("item_id")]
        public string ItemId;

        [JsonProperty("qty")]
        public int Qty;
    }

    [Serializable]
    public class InventoryResponse
    {
        [JsonProperty("status")]
        public string Status;

        [JsonProperty("data")]
        public InventoryData Data;
    }

    [Serializable]
    public class InventoryData
    {
        [JsonProperty("session_id")]
        public string SessionId;

        [JsonProperty("items")]
        public InventoryItemDto[] Items;
    }
}