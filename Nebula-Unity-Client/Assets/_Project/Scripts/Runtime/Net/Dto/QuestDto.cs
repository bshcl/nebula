using Newtonsoft.Json;
using System;

namespace Nebula.Net
{
    [Serializable]
    public class QuestClaimResponse
    {
        [JsonProperty("status")]
        public string Status;

        [JsonProperty("data")]
        public QuestClaimData Data;
    }

    [Serializable]
    public class QuestClaimData
    {
        [JsonProperty("quest_id")]
        public string QuestId;

        [JsonProperty("status")]
        public string QuestStatus;

        [JsonProperty("grant")]
        public QuestGrantDto Grant;

        [JsonProperty("mood")]
        public int Mood;
    }

    [Serializable]
    public class QuestGrantDto
    {
        [JsonProperty("item_id")]
        public string ItemId;

        [JsonProperty("granted_qty")]
        public int GrantedQty;
    }

    /// <summary>
    /// Response for GET status / POST ready (no grant payload).
    /// </summary>
    [Serializable]
    public class QuestStatusResponse
    {
        [JsonProperty("status")]
        public string Status;

        [JsonProperty("data")]
        public QuestStatusData Data;
    }

    [Serializable]
    public class QuestStatusData
    {
        [JsonProperty("quest_id")]
        public string QuestId;

        [JsonProperty("title")]
        public string Title;

        [JsonProperty("status")]
        public string QuestStatus;

        [JsonProperty("reward_item_id")]
        public string RewardItemId;

        [JsonProperty("mood_delta")]
        public int MoodDelta;
    }
}
