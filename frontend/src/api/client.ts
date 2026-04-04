import axios from "axios";
import { supabase } from "@/api/supabase";

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
