## 2070c1d - 2025-06-08
- history heuristic approach

## 2c0045d - 2025-06-06
- Refactor transcription logging, enhance subtitle export formatting, and improve error handling in subprocess calls.

## 2f6996c - 2025-06-06
- Update version to 1.0.8, refactor timestamp formatting, enhance transcription output with estimated duration, and improve user feedback during processing.

## c81eae6 - 2025-06-06
- Enhance transcription process by adding estimated duration display and improving user feedback with real-time progress updates. Update error handling in subprocess calls and refine output formatting for transcription results.

## 88691b0 - 2025-06-05
- Update version to 1.0.7, add audio metadata extraction and duration estimation functions, improve error handling, and enhance user feedback during transcription process.

## f1efdf3 - 2025-06-05
- Update timestamp format

## 1ca1bba - 2025-06-05
- Update version to 1.0.6, enhance filename formatting in save_transcription_result, and improve error handling in file drop functionality. Added user feedback during transcription initiation.

## 7b839c8 - 2025-06-04
- Refactor file drop handling to streamline transcription initiation and improve error handling for FFmpeg checks.

## 0e22ab8 - 2025-06-04
- Update silence removal parameters in FFmpeg command for improved audio processing accuracy.

## 3b9afb3 - 2025-06-04
- Remove unnecessary comments

## df71aac - 2025-06-04
- Update .gitignore to include transcriptions directory and ensure proper formatting of existing entries.

## 82b75d4 - 2025-06-04
- Update version number to 1.0.5

## 2342b2b - 2025-06-04
- Refactor save_transcription_result to create a dedicated output directory for transcriptions and format output filenames with date and base name. This improves organization and clarity of saved files.

## 395f8ce - 2025-06-04
- Add silence removal functionality using FFmpeg before transcription, enhancing the transcription process.

## 486c764 - 2025-06-04
- Enhance transcription function with FFmpeg check and improved debug logging. Added user feedback during processing and ensured verbose output for transcription results.

## f6ea6d5 - 2025-06-04
- + README + Deleted unused file

## f600243 - 2025-06-04
- Update README.md to enhance clarity and formatting. Improved descriptions of features, installation instructions, and added a quick guide for Windows installation. Adjusted formatting for better readability and consistency.

## 7e85959 - 2025-06-04
- Add debug print statements in the transcription function to log the file being processed and its existence check, aiding in troubleshooting.

## ad9ddda - 2025-06-04
- Add debug print statement for dropped file data in drag-and-drop handler to assist with troubleshooting.

## 4c32f7c - 2025-06-04
- Enhanced drag-and-drop handling to support multiple file inputs more robustly and improves error handling for invalid or missing files.

## f8af15d - 2025-06-04
- Add drag-and-drop functionality for file input and update GUI initialization to use TkinterDnD. Enhanced application description in the header comment.

## 99a919b - 2025-06-04
- ✅ Auto language detection ✅ Drag & drop ✅ Option to open output folder μετά την αποθήκευση ✅ Remember last format selected	(config.json) ✅ Error logging σε αρχείο (errors.log με traceback) ✅ Export to clipboard ✅ Προσθήκη Command Line Support

## 9e3f451 - 2025-06-04
- Refine error handling in transcription function to catch specific exceptions

## 5f4751f - 2025-06-04
- Add versioning and enhance transcription UI with progress indication and error handling

## 1b604cb - 2025-06-04
- Added threading mechanism for the transcription process to prevent UI blocking during long operations.

## 84267f5 - 2025-06-04
- Improve error handling in transcription function by specifying exception types

## 1c67da6 - 2025-06-04
- Refactor transcription logic and enhance GUI for audio file processing

## 1ce5770 - 2025-06-04
- main app

## 707cb1d - 2025-06-04
- Create README.md

## edf7586 - 2025-06-04
- Initial commit
