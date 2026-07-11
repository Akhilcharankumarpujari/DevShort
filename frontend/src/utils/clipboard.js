import toast from "react-hot-toast";

/**
 * Copies the given text to the clipboard.
 * Uses navigator.clipboard if available, otherwise falls back to document.execCommand.
 * Shows a success toast on success, or a failure toast if both copy methods fail.
 * Never crashes the application.
 */
export async function copyToClipboard(text) {
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
      return true;
    } catch (err) {
      console.warn("navigator.clipboard.writeText failed, trying fallback: ", err);
    }
  }

  // Fallback using document.execCommand
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Avoid scrolling to bottom, keep invisible
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    
    if (successful) {
      toast.success("Copied to clipboard!");
      return true;
    } else {
      toast.error("Copy failed. Please copy manually.");
      return false;
    }
  } catch (err) {
    console.error("Fallback copy failed: ", err);
    toast.error("Copy failed. Please copy manually.");
    return false;
  }
}
