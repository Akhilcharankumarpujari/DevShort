import { customAlphabet } from "nanoid";
import config from "../config/index.js";

const ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

const generateShortCode = customAlphabet(ALPHABET, config.shortCodeLength);

export { generateShortCode };
