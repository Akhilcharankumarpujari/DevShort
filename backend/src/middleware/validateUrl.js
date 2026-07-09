import { BadRequestError } from "../utils/apiError.js";

const URL_REGEX = /^https?:\/\/.+/i;
const MAX_URL_LENGTH = 2048;

function validateUrl(req, _res, next) {
  const { url } = req.body;

  if (!url || typeof url !== "string") {
    throw new BadRequestError("URL is required and must be a string");
  }

  const trimmed = url.trim();

  if (!trimmed) {
    throw new BadRequestError("URL cannot be empty");
  }

  if (trimmed.length > MAX_URL_LENGTH) {
    throw new BadRequestError(`URL must be ${MAX_URL_LENGTH} characters or less`);
  }

  if (!URL_REGEX.test(trimmed)) {
    throw new BadRequestError("URL must start with http:// or https://");
  }

  req.body.url = trimmed;
  next();
}

export default validateUrl;
