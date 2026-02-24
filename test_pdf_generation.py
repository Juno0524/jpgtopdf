import os
import unittest
from unittest.mock import MagicMock
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
# import the module to test (assuming it's in the same directory)
import sys
sys.path.append(os.getcwd())
from jpg_to_pdf_converter import JpgToPdfConverterApp
import tkinter as tk

class TestPdfGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create dummy images
        cls.img1_path = "test_image1.jpg"
        cls.img2_path = "test_image2.jpg"
        
        img1 = Image.new('RGB', (100, 100), color = 'red')
        img1.save(cls.img1_path)
        
        img2 = Image.new('RGB', (200, 150), color = 'blue')
        img2.save(cls.img2_path)
        
        cls.output_pdf = "test_output.pdf"

    @classmethod
    def tearDownClass(cls):
        # Clean up
        if os.path.exists(cls.img1_path):
            os.remove(cls.img1_path)
        if os.path.exists(cls.img2_path):
            os.remove(cls.img2_path)
        if os.path.exists(cls.output_pdf):
            pass # Keep execution artifact for review if needed, or delete

    def test_pdf_creation(self):
        # Mock Tkinter root
        root = tk.Tk()
        app = JpgToPdfConverterApp(root)
        
        # Set dummy data
        app.campaign_code.set("TEST-CODE-001")
        app.usage_content.set("테스트/Verification")
        app.pickup_date.set("2023-11-01")
        app.delivery_date.set("2023-11-02")
        app.image1_path.set(self.img1_path)
        app.image2_path.set(self.img2_path)
        
        # Verify mocked file exist
        self.assertTrue(os.path.exists(app.image1_path.get()))
        self.assertTrue(os.path.exists(app.image2_path.get()))
        
        # Run generation
        try:
            app.create_pdf(self.output_pdf)
            print(f"PDF generated at {self.output_pdf}")
        except Exception as e:
            self.fail(f"PDF generation failed with error: {e}")
            
        self.assertTrue(os.path.exists(self.output_pdf))
        
        # Check PDF size (basic check)
        self.assertGreater(os.path.getsize(self.output_pdf), 1000)
        
        root.destroy()

if __name__ == '__main__':
    unittest.main()
