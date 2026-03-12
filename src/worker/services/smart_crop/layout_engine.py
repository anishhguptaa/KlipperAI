from typing import Tuple, Dict, Any

class LayoutEngine:
    """
    Decides how to fit an important region into a target 9:16 frame.
    """

    def __init__(self, target_aspect_ratio: float = 9/16):
        self.target_aspect_ratio = target_aspect_ratio

    def calculate_crop_window(
        self, 
        union_bbox: Tuple[int, int, int, int], 
        frame_width: int, 
        frame_height: int
    ) -> Tuple[int, int, int, int]:
        """
        Determines the crop window. 
        
        If the region fits well into 9:16 (Case 1), it expands the box to match 9:16 exactly (Standard Crop).
        If not (Case 2/3), it returns the tight box (plus margin), implying padding will be needed.

        Args:
            union_bbox: (x1, y1, x2, y2) of the important region.
            frame_width: Width of the source frame.
            frame_height: Height of the source frame.

        Returns:
            Tuple (x1, y1, x2, y2) - The region to cut from source.
        """
        
        ux1, uy1, ux2, uy2 = union_bbox
        region_w = ux2 - ux1
        region_h = uy2 - uy1
        
        # Add a margin (e.g., 10%)
        margin_w = int(region_w * 0.1)
        margin_h = int(region_h * 0.1)
        
        cx1 = max(0, ux1 - margin_w)
        cy1 = max(0, uy1 - margin_h)
        cx2 = min(frame_width, ux2 + margin_w)
        cy2 = min(frame_height, uy2 + margin_h)
        
        # Current dimensions
        w = cx2 - cx1
        h = cy2 - cy1
        
        if w == 0 or h == 0:
             return self.get_fallback_crop(frame_width, frame_height)

        current_ratio = w / h
        
        # Check if we can/should force a 9:16 crop (Case 1)
        # We define "fits well" if the content isn't extremely wide or extremely tall
        # and if expanding it to 9:16 doesn't exceed frame boundaries too much.
        # Actually, let's try to expand to 9:16.
        
        # Target dimensions if we force 9:16
        # We want to Enclose the current box.
        # So we need a box with ratio 9/16 that contains (w, h).
        
        # If current is wider than target (e.g. 1:1 vs 9:16), 
        # to enclose it in 9:16, we must increase HEIGHT.
        # new_h = w / (9/16)
        
        # If current is narrower than target (e.g. 1:4 vs 9:16),
        # to enclose it, we must increase WIDTH.
        # new_w = h * (9/16)
        
        if current_ratio > self.target_aspect_ratio:
            # Case: Region is wider than 9:16.
            # To make it 9:16, we would need to add vertical space (increase height).
            req_h = w / self.target_aspect_ratio
            if req_h <= frame_height:
                # We can expand vertically to fit 9:16!
                # This corresponds to "Case 1" (Standard Crop) where we just show more vertical context.
                # However, if req_h is huge (bigger than frame), we can't.
                center_y = (cy1 + cy2) / 2
                half_h = req_h / 2
                new_y1 = int(center_y - half_h)
                new_y2 = int(center_y + half_h)
                
                # Clamp and shift if needed
                if new_y2 - new_y1 <= frame_height:
                    if new_y1 < 0:
                        new_y2 -= new_y1
                        new_y1 = 0
                    if new_y2 > frame_height:
                        new_y1 -= (new_y2 - frame_height)
                        new_y2 = frame_height
                        
                    # Final check
                    if new_y1 >= 0 and new_y2 <= frame_height:
                         return (cx1, new_y1, cx2, new_y2)

            # If we reached here, we couldn't expand height enough (it would go out of bounds).
            # So we must stick to the wide aspect ratio and accept padding (Case 2).
            return (cx1, cy1, cx2, cy2)

        else:
            # Case: Region is narrower (taller) than 9:16.
            # To make it 9:16, we need to add horizontal space (increase width).
            req_w = h * self.target_aspect_ratio
            if req_w <= frame_width:
                # We can expand horizontally!
                center_x = (cx1 + cx2) / 2
                half_w = req_w / 2
                new_x1 = int(center_x - half_w)
                new_x2 = int(center_x + half_w)
                
                if new_x2 - new_x1 <= frame_width:
                    if new_x1 < 0:
                        new_x2 -= new_x1
                        new_x1 = 0
                    if new_x2 > frame_width:
                        new_x1 -= (new_x2 - frame_width)
                        new_x2 = frame_width
                    
                    if new_x1 >= 0 and new_x2 <= frame_width:
                        return (new_x1, cy1, new_x2, cy2)
            
            # If we can't expand width, we accept padding (Case 3 - rare for 9:16 target unless extremely tall).
            return (cx1, cy1, cx2, cy2)

    def get_fallback_crop(self, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Returns a center crop 9:16."""
        target_w = int(frame_height * self.target_aspect_ratio)
        if target_w > frame_width:
            # Frame is narrower than 9:16 (e.g. already vertical but thin?)
            # Just return full frame
            return (0, 0, frame_width, frame_height)
            
        x1 = (frame_width - target_w) // 2
        return (x1, 0, x1 + target_w, frame_height)

