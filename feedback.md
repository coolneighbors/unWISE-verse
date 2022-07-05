# Cool Neighbors Testing Feedback
This document provides a list of feedback from various Cool Neighbors tests. Feedback is in approximately chronological order.

## Alpha-0 Test
### User: Herakles
Because we always have to think from the point of view of beginners and not of an advanced user, I think the following information (metadata) would be helpful. These are all good tools to identify the movement of an object unless it is obvious.

(one link each with centered view on the image section)

WiseView link
SIMBAD Link (optional)
VizieR Link (optional)
IRSA Finder Chart Link
Legacy Surveys Sky Viewer (optional)
and to be a bit different than BYW maybe a CatWISE2020 Catalog Link with a search radius of maybe 0.5 arcmin (like this example).

SIMBAD, VizieR and Legacy Surveys would be optional because these pages are also accessible via WiseView. Then there would also be room for other information. All the other information - I think - is not really helpful, at least not for someone who doesn't know anything about it like I do but maybe you need the data?

These are my thoughts.
cheers

### User: jrchem
Can the classification images be made larger? On my wide LCD screen, they are rather small. The box with the response buttons is actually larger than them and both are surrounded by lots of blank gray space. The menu and new announcements strips also seem to be wider (taller) than they need to be. On my old CRT monitor, image and response box get displayed somewhat larger, so the screen space is used more effectively. But the images are still noticeably smaller than those in BYW/P9 classification and the header strips remain wider than necessary.

Also, it would help if the animation ran continuously unless intentionally paused. The current three times through the loop probably won’t be enough except for easy subjects.

### User: Herakles
Hi @austinh2001
Can it happen that there is more than one moving object on the image? For example, a pair of brown dwarfs (binary thing).
If this case could happen, i would recommend to add an additional button to report more than one moving object.

cheers

### User: jrchem
Hi @austin2001,
I see you have the continuous scan feature implemented. It looks good! Here are a couple more comments/questions:
• I can see more detail in the Classify images on my old CRT monitor than on my LCD unit, but even on the CRT they look sufficiently washed out that I’m not sure I’m seeing the target object. Perhaps that is because none of the ones I’ve seen so far contain a mover, but it reinforces the desire for exposure control.
• One of the Subjects I was presented had a grid overlay as was talked about on last week’s Zoom call. I can see how this could be helpful, but not being sure I am seeing what I’m supposed to anyway it would have been nice to toggle it off temporarily so I could see behind the lines. Could a feature like that be arranged?
• If I understood comments made on Thursday, target objects will generally be around the middle of the presented field, but not necessarily in the exact center. Is that correct? If so, is there a way to illustrate the portion of the field within which the target under investigation is likely to be located (perhaps as an illustration in the Tutorial or Field Guide if the range is pretty much the same for all subjects)? Or is there concern that this would lessen incentive for the good practice of examining the whole field in case things like “the Accident” show up?
• Has a “Skip middle epochs” setting like Wiseview has been considered? That can make motion easier to spot. On the other hand, it can lead to noise-induced false positives, so I’m not sure it would be worth adding here – just raising it as something to think about.
• Also, one question: Should moving objects in these subjects jump farther between the first and second epochs than between subsequent ones due to the WISE pre/post data gap?
Thanks.

Addendum: I see that it is possible to switch directly back and forth between Frames 1 and 10 using the arrow keys. So no need to generate a "Skip middle epochs" feature.

### User: Heracles
I agree with Jim (@jrchem) now that i have classified the set.

I would prefer the larger image size (387 x 387 px) for classification. Who needs it even bigger, can enlarge via +

A grid can be helpful, but it also hides a lot unless it can be switched off. A solution within the classifier would of course be optimal. As a transitional solution, perhaps this would be helpful. For example, you can install a small additional program on your computer such as Meazure 2.0. Here you can lay a grid over the whole screen, change the grid size and turn it on and off (maybe there is a better one, that was just quickly picked and tried out). You also have a magnifying glass with it! Remember back then at BYW (before WiseView) we used a programm named "Crosshair" to read the coordinates from the flipbooks 😁

Example Alt Text

At the current exposure setting, candidates such as those in subject 77401249 are really hard to spot. Maybe you should optimize the image setting according to these faint objects if we have no way to change the setting in the classification layer. A bit sharper and darker would be good. The "invert Image" button only helps to a limited extent. However, this could probably turn into the opposite again at crowded sky sections (near the galactic plane - as long as you will also use image sections of this part of the sky) because the images have to be brightened again.
I'm sure you will find a solution. Otherwise, everything looks good except for the points mentioned!

cheers

### User: jrchem

Regarding grid alternatives, would eliminating everything except tiny plus signs at the intersection points leave enough of a framework to be sufficient?
Dan Caselden has often mentioned the difficulty in trying to select appropriate settings depending on the type of sky area, so you have your work cut out for you there. Being able to get the subjects adjusted properly in some manner would be by far the best approach. But if that proves impossible, Jörg's suggestion of having a link to the Wiseview image on the metadata page would at least provide a way to access the exposure controls current volunteers probably know best right now. If that ends up being implemented, the technique should be mentioned in the FAQ file as a way to deal with hard to see subjects.

### User: Herakles
First of all, you classified the entire set? If so, great work!
Thanks Austin but hey there were only 53 subjects - that was done before breakfast 😂 -> need more

Secondly, the large image is definitely our current working back-end version...
Thanks for clarification this Point. A smaller field of view means we can miss less and get more images but will need more time to work through everything. I personally like larger FOV's because movements show up better, but let's see how it works.

Thirdly, we have been trying to work with Zooniverse to try and have a sort of overlay-image/grid button be implemented but it seems that at this current date they are not able to do such a thing (for x, y, and z reasons).
If i remember the beginnings of BYW there were similar wishes but a customization was not possible back then either. I think we will have to resign ourselves to the modular principle and accept what is offered on zooniverse. If you have a solution, show it to us and we can all decide together whether a grid is necessary or not.

Fourthly, we have mainly been focusing on the actual importing of the data, but not the modification of the data for things like adjusting the "contrast".
As Jim has already mentioned, there will certainly not be an all-encompassing solution. We know that, unless you are able to create one. Then it could be that we will propose you for the next NASA award 😎

cheers


## Alpha-1 Test

### User: jrchem

Hi @NoahSchapera.9 and @austinh2001,
I've been through several subjects from the new alpha test, and here are a few comments and questions on what I've run into so far. Most are pretty minor.

Image size looks good now.
The subject number doesn't show up in Classify. Will it be there in the final version? If not, it should be included on the metadata page so it can be recorded in case the subject is lost before Done or Done & Talk are pushed.
The grids in these examples actually look OK to me. Because they run along the pixel edges, you can see they aren't hiding anything. But if they are still a distraction for some, I think they could be cut back to just plus signs with one pixel long arms at the grid intersection points.
Could the default blink interval in the Wiseview link be reduced? 500 ms is awfully slow.
The field of view in the IRSA link does not match what is shown the flipbook or Wiseview, but I find that helpful. There are times when it is helpful to easily see a larger area, and IRSA can always be zoomed in at will if desired.
My classification procedure has been to first examine the flipbook for indications and direction of motion. I then go to Wiseview to check whether exposure adjustments reveal anything new. Finally, if movement is questionable, I check for position shifts over time in IRSA and proper motion data in VizieR. My conclusion for several flipbooks has been that I can't positively say there is motion, but if there is, it is in direction X. In every case so far, IRSA and VizieR have confirmed that guess, so I have responded YES to the movement question (I would have answered NO if directions differed). Is that the desired answer in such cases, or should the answer be NO unless the flipbook itself shows unquestionable evidence of motion? Also, every subject I've looked at so far has shown motion. If these test subjects are typical of the entire final set, will it be necessary to include some random sky areas to hit the positivity sweet spot Marc mentioned last week?


