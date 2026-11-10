"""
Bed Management Service.
Handles wards, bed types, availability status, and anti-double-allocation locking.
"""

from typing import List, Dict, Any, Optional, Tuple
from database.connection import Database

class BedService:
    """Manages hospital beds, wards, occupancy states, and allocation integrity."""

    @classmethod
    def get_all_beds(
        cls,
        ward: Optional[str] = None,
        bed_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves beds with optional filtering by ward, type, or occupancy status."""
        with Database() as db:
            conditions = []
            params = []

            if ward and ward != "All":
                conditions.append("ward_name = %s")
                params.append(ward)

            if bed_type and bed_type != "All":
                conditions.append("bed_type = %s")
                params.append(bed_type)

            if status and status != "All":
                conditions.append("status = %s")
                params.append(status)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT bed_id, bed_number, ward_name, bed_type, daily_charge, status, notes, created_at
                FROM beds
                {where_clause}
                ORDER BY ward_name ASC, bed_number ASC
            """
            return db.execute_query(query, tuple(params))

    @classmethod
    def get_available_beds(cls, ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches only currently Available beds."""
        return cls.get_all_beds(ward=ward, bed_type=bed_type, status="Available")

    @classmethod
    def get_bed_by_id(cls, bed_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific bed record."""
        with Database() as db:
            return db.execute_one("SELECT * FROM beds WHERE bed_id = %s", (bed_id,))

    @classmethod
    def create_bed(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Creates a new hospital bed."""
        bed_number = data.get("bed_number", "").strip().upper()
        ward_name = data.get("ward_name", "").strip()
        bed_type = data.get("bed_type", "General")
        daily_charge = float(data.get("daily_charge") or 500.0)

        if not bed_number or not ward_name:
            return False, "Bed number and ward name are required.", None

        try:
            with Database() as db:
                # Check for duplicate bed number
                exists = db.execute_one("SELECT bed_id FROM beds WHERE bed_number = %s", (bed_number,))
                if exists:
                    return False, f"Bed '{bed_number}' already exists.", None

                query = """
                    INSERT INTO beds (bed_number, ward_name, bed_type, daily_charge, status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (bed_number, ward_name, bed_type, daily_charge, data.get("status", "Available"), data.get("notes", "").strip() or None)
                bed_id = db.execute_insert(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("BED_CREATED", "Bed", bed_number, f"Created {bed_type} bed in ward {ward_name}")
                )
                return True, f"Bed {bed_number} created successfully.", bed_id
        except Exception as e:
            return False, f"Failed to create bed: {str(e)}", None

    @classmethod
    def update_bed(cls, bed_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Updates bed attributes."""
        bed_number = data.get("bed_number", "").strip().upper()
        ward_name = data.get("ward_name", "").strip()
        bed_type = data.get("bed_type", "General")
        status = data.get("status", "Available")
        daily_charge = float(data.get("daily_charge") or 500.0)

        if not bed_number or not ward_name:
            return False, "Bed number and ward name are required."

        try:
            with Database() as db:
                # If setting to Available when it's tied to an active admission, prevent conflict
                if status == 'Available':
                    active_adm = db.execute_one(
                        "SELECT admission_id FROM admissions WHERE bed_id = %s AND status = 'Admitted'",
                        (bed_id,)
                    )
                    if active_adm:
                        return False, "Cannot set bed status to 'Available' while an active patient admission is assigned to it. Discharge patient first."

                query = """
                    UPDATE beds
                    SET bed_number = %s, ward_name = %s, bed_type = %s,
                        daily_charge = %s, status = %s, notes = %s
                    WHERE bed_id = %s
                """
                params = (bed_number, ward_name, bed_type, daily_charge, status, data.get("notes", "").strip() or None, bed_id)
                db.execute_non_query(query, params)
                return True, "Bed updated successfully."
        except Exception as e:
            return False, f"Failed to update bed: {str(e)}"

    @classmethod
    def delete_bed(cls, bed_id: int) -> Tuple[bool, str]:
        """Deletes a bed if it has no active or historical admission constraints."""
        try:
            with Database() as db:
                active_adm = db.execute_one("SELECT admission_id FROM admissions WHERE bed_id = %s", (bed_id,))
                if active_adm:
                    return False, "Cannot delete bed: Historical or active admissions are associated with this bed."

                bed = db.execute_one("SELECT bed_number FROM beds WHERE bed_id = %s", (bed_id,))
                bed_num = bed['bed_number'] if bed else str(bed_id)

                db.execute_non_query("DELETE FROM beds WHERE bed_id = %s", (bed_id,))
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("BED_DELETED", "Bed", bed_num, f"Deleted bed ID {bed_id}")
                )
                return True, "Bed deleted successfully."
        except Exception as e:
            return False, f"Failed to delete bed: {str(e)}"

    @classmethod
    def allocate_bed(cls, bed_id: int) -> Tuple[bool, str]:
        """
        Marks a bed as Occupied with atomic check to prevent double allocation.
        """
        try:
            with Database() as db:
                bed = db.execute_one("SELECT bed_number, status FROM beds WHERE bed_id = %s FOR UPDATE", (bed_id,))
                if not bed:
                    return False, "Bed not found."
                if bed['status'] == 'Occupied':
                    return False, f"Double-allocation prevented: Bed {bed['bed_number']} is already occupied."
                if bed['status'] == 'Maintenance':
                    return False, f"Bed {bed['bed_number']} is currently under maintenance and cannot be allocated."

                db.execute_non_query("UPDATE beds SET status = 'Occupied' WHERE bed_id = %s", (bed_id,))
                return True, f"Bed {bed['bed_number']} allocated successfully."
        except Exception as e:
            return False, f"Bed allocation failed: {str(e)}"

    @classmethod
    def release_bed(cls, bed_id: int) -> Tuple[bool, str]:
        """Releases a bed back to Available state."""
        try:
            with Database() as db:
                bed = db.execute_one("SELECT bed_number FROM beds WHERE bed_id = %s", (bed_id,))
                db.execute_non_query("UPDATE beds SET status = 'Available' WHERE bed_id = %s", (bed_id,))
                bed_num = bed['bed_number'] if bed else str(bed_id)
                return True, f"Bed {bed_num} released to Available."
        except Exception as e:
            return False, f"Bed release failed: {str(e)}"

    @classmethod
    def get_ward_summary(cls) -> List[Dict[str, Any]]:
        """Calculates total, occupied, available, and occupancy % grouped by ward."""
        with Database() as db:
            query = """
                SELECT 
                    ward_name,
                    COUNT(*) as total_beds,
                    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available_beds,
                    SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied_beds,
                    SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance_beds,
                    ROUND((SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1) as occupancy_rate
                FROM beds
                GROUP BY ward_name
                ORDER BY ward_name ASC
            """
            return db.execute_query(query)
