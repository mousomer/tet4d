using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Tet4D.UnityReplay.TraceReplay
{
    internal static class TraceJson
    {
        public static JObject ParseObject(string jsonText)
        {
            return JObject.Parse(jsonText);
        }

        public static JObject GetObject(JToken token, string path)
        {
            if (token == null)
            {
                return null;
            }

            return token.SelectToken(path) as JObject;
        }

        public static JArray GetArray(JToken token, string path)
        {
            if (token == null)
            {
                return null;
            }

            return token.SelectToken(path) as JArray;
        }

        public static string GetString(JToken token, string path, string fallback = "")
        {
            if (token == null)
            {
                return fallback;
            }

            JToken value = token.SelectToken(path);
            if (value == null || value.Type == JTokenType.Null)
            {
                return fallback;
            }

            return value.Value<string>() ?? fallback;
        }

        public static int GetInt(JToken token, string path, int fallback = 0)
        {
            if (token == null)
            {
                return fallback;
            }

            JToken value = token.SelectToken(path);
            if (value == null || value.Type == JTokenType.Null)
            {
                return fallback;
            }

            int parsed;
            return int.TryParse(value.ToString(), out parsed) ? parsed : fallback;
        }

        public static float GetFloat(JToken token, string path, float fallback = 0f)
        {
            if (token == null)
            {
                return fallback;
            }

            JToken value = token.SelectToken(path);
            if (value == null || value.Type == JTokenType.Null)
            {
                return fallback;
            }

            float parsed;
            return float.TryParse(value.ToString(), out parsed) ? parsed : fallback;
        }

        public static bool GetBool(JToken token, string path, bool fallback = false)
        {
            if (token == null)
            {
                return fallback;
            }

            JToken value = token.SelectToken(path);
            if (value == null || value.Type == JTokenType.Null)
            {
                return fallback;
            }

            bool parsed;
            return bool.TryParse(value.ToString(), out parsed) ? parsed : fallback;
        }

        public static int[] GetIntArray(JToken token, string path)
        {
            return GetIntArray(token.SelectToken(path) as JArray);
        }

        public static int[] GetIntArray(JArray array)
        {
            if (array == null)
            {
                return new int[0];
            }

            int[] values = new int[array.Count];
            for (int index = 0; index < array.Count; index += 1)
            {
                values[index] = array[index].Value<int>();
            }

            return values;
        }

        public static float[] GetFloatArray(JToken token, string path)
        {
            return GetFloatArray(token.SelectToken(path) as JArray);
        }

        public static float[] GetFloatArray(JArray array)
        {
            if (array == null)
            {
                return new float[0];
            }

            float[] values = new float[array.Count];
            for (int index = 0; index < array.Count; index += 1)
            {
                values[index] = array[index].Value<float>();
            }

            return values;
        }

        public static string ToSummary(JToken token, int maxLength = 420)
        {
            if (token == null)
            {
                return string.Empty;
            }

            string text = token.ToString(Formatting.None);
            if (text.Length <= maxLength)
            {
                return text;
            }

            return text.Substring(0, maxLength - 3) + "...";
        }

        public static List<string> StringListFromArray(JArray array)
        {
            List<string> values = new List<string>();
            if (array == null)
            {
                return values;
            }

            foreach (JToken token in array)
            {
                values.Add(token.Value<string>() ?? string.Empty);
            }

            return values;
        }
    }
}
