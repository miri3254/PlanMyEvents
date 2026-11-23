from pypdf import PdfReader

from app.schemas.event import EventCreate
from app.utils.pdf_generator import generate_delivery_sheet_pdf


def test_delivery_fields_are_accepted_by_event_schema():
    event = EventCreate(
        name="אירוע בדיקה",
        menu_type="תפריט שבת",
        date="2026-06-28T12:00:00",
        venue_name="אולם בדיקה",
        delivery_contents_notes="שתייה, לחמניות ומפות",
        last_minute_items="קינוחים מהמקפיא",
    )

    assert event.venue_name == "אולם בדיקה"
    assert event.delivery_contents_notes == "שתייה, לחמניות ומפות"
    assert event.last_minute_items == "קינוחים מהמקפיא"


def test_delivery_pdf_is_generated_with_multiple_pages_when_needed():
    event_data = {
        "name": "אירוע בדיקה",
        "event_time": "18:30",
        "venue_name": "אולם בדיקה",
        "address": "רחוב הבדיקה 1",
        "city": "ירושלים",
        "floor": 2,
        "has_elevator": True,
        "access_code": "1234",
        "onsite_contact_name": "איש קשר",
        "onsite_contact_phone": "050-0000000",
        "dishware_type": "כלים אמיתיים",
        "delivery_contents_notes": "שתייה, לחמניות, מפות וכלי מלצר",
        "last_minute_items": "קינוחים מהמקפיא",
        "equipment_dropoff_location": "מטבח האולם",
        "boxes": [
            {"box_type": f"ארגז {index}", "quantity": index, "notes": "לבדיקה"}
            for index in range(1, 9)
        ],
        "total_boxes": 36,
        "check_refrigerator": True,
        "check_freezer": True,
        "delivery_notes": [{"note": "לבדוק לחמניות"}],
        "delivery_special_notes": "יש להתקשר בהגעה",
    }

    pdf = generate_delivery_sheet_pdf(
        event_data,
        "28/06/2026",
        event_sequence_label="אירוע #2",
        event_sequence_color="green",
    )

    contents = pdf.getvalue()
    assert contents.startswith(b"%PDF")
    assert len(contents) > 10_000
    assert len(PdfReader(pdf).pages) >= 1
