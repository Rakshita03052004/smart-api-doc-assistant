// frontend/src/api.js
import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

export const parseSpec = async (specData) => {
  try {
    const res = await axios.post(`${BASE_URL}/parse-spec`, specData);
    return res.data;
  } catch (err) {
    console.error(err);
    return null;
  }
};