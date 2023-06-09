# Cool Neighbors Testing History
This document provides a history of cool neighbors testing and related pipeline development.

## Alpha-0 Test
### Background: 
We are unable to independently access the pixel values of each frame we download from WiseView. As a result, it is difficult to determine optimum minbright / maxbright parameters for our target uploads. 

### Setup
In order to determine which brightness levels lead to the most accurate classifications, we uploaded a 3 subect sets of 10 targets each. In each set, we included 8 random fields and 2 known movers from previous brown dwarf lists. In set 1, we used a minbright value of -10, in set 2 a minbright value of -20, and in set 3 a minbright value of -30.  We used a retirement classification for each subject of 3. Volunteers were asked to determine whether there were any moving objects in each frame and were able to reference other datablases using the provided RA and DEC.

### Analysis
Of the 91 classifications in this test, 89 were accurate leading to an overall accuracy of around 97%. The classifications were completed in a roughly 2 day period, much faster than expected. 

Both incorrrect classifications were from the minbright=-10 subject set. One was a  false positive classification, while one was a false negative classification. Both the minbright=-20 and minbright=-30 subject sets were 100% accurate.

Volunteers feedback from this test was that the images were generally too bright to properly analyze. In addition, volunteers noted that the addition of a grid would be helpful in identifying whether an object was moving consistently across multiple frames. 

Due to the small sample size in this test, we were unable to make broad decisions about the optimum brightness parameters in future data uploads. However, its likely that the minbright parameter wil be increased to at least -20 or above.

## Alpha-1 Test
### Background
Following the Alpha-0 Test, it became apparent that a larger sample size was needed in order to generate meaningful data about future uploads. The Alpha-1 test is intended to represent a scale-model of the final Cool Neighbors project incoprporating feedback from the Alpha-0 test in order to uncover possible flaws and generate more significant test data. 

### Setup
Subjects were chosen from the first 500 targets in Dan's machine learning target document.

Subjects were uploaded via the zooniverse pipeline to a subect set and assigned to a new workflow. The only meaningful change in this new workflow was the increased retirement number to 6 and the question being reformatted to say "Are there any movers in this frame" rather than "Are there any moving objects in this frame." The minbright parameter was set at -30 while maxbright was set at 150. The FOV was 120 arcseconds, anda 10x10 grid was overlayed onto each image.

New metadata fields were added for the Julian date of each frame, and links to various astronomical databases were reformatted to be more readable. 


