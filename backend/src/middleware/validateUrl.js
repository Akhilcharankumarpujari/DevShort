import { BadRequestError } from "../utils/apiError.js";

const URL_REGEX = /^https?:\/\/.+/i;
const MAX_URL_LENGTH = 2048;
const CUSTOM_ALIAS_REGEX = /^[a-zA-Z0-9_-]{4,30}$/;

function validateUrl(req, _res, next) {
  const { url, customAlias, expiresAt } = req.body;

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

  // Validate custom alias if provided
  if (customAlias !== undefined && customAlias !== null && customAlias !== "") {
    if (typeof customAlias !== "string" || !CUSTOM_ALIAS_REGEX.test(customAlias)) {
      throw new BadRequestError(
        "Custom alias must be 4-30 characters using letters, numbers, hyphens, and underscores"
      );
    }
  }

  // Validate expiresAt if provided
  if (expiresAt !== undefined && expiresAt !== null && expiresAt !== "") {
    const date = new Date(expiresAt);
    if (isNaN(date.getTime())) {
      throw new BadRequestError("Invalid expiration date");
    }
    if (date <= new Date()) {
      throw new BadRequestError("Expiration date must be in the future");
    }
  }

  next();
}

export default validateUrl;
