# services/offline.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image, ListFlowable, ListItem
from datetime import datetime
from typing import Dict, List, Any
import os

class ServiceOrderPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor('#2E5090')
        ))
        
        self.styles.add(ParagraphStyle(
            name='Normal-Indent',
            parent=self.styles['Normal'],
            leftIndent=20,
            spaceBefore=6,
            spaceAfter=6
        ))
    
    def _create_header(self, doc: SimpleDocTemplate) -> List:
        """Creates the document header."""
        elements = []
        
        # Add company logo if exists
        if os.path.exists('assets/logo.png'):
            img = Image('assets/logo.png', width=2*cm, height=2*cm)
            elements.append(img)
        
        # Add title and date
        elements.append(Paragraph(
            f"ORDEM DE SERVIÇO - {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _create_equipment_table(self, equipments: List[Dict[str, Any]]) -> Table:
        """Creates a formatted table for equipment list."""
        if not equipments:
            return None
            
        # Table header
        data = [['Código SAP', 'Descrição', 'Quantidade']]
        
        # Table data
        for equip in equipments:
            data.append([
                equip['codigo_sap'],
                equip['descricao'],
                str(equip['quantidade'])
            ])
            
        # Create and style the table
        table = Table(data, colWidths=[3*cm, 10*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        return table
    
    def _create_safety_measures_list(self, measures: List[str]) -> ListFlowable:
        """Creates a formatted list of safety measures."""
        items = []
        for measure in measures:
            items.append(ListItem(
                Paragraph(measure, self.styles['Normal']),
                value='bullet'
            ))
        return ListFlowable(
            items,
            bulletType='bullet',
            leftIndent=35,
            bulletFontSize=8,
            bulletOffsetY=2
        )
    
    def generate_pdf(self, service_order: Dict[str, Any], output_path: str) -> str:
        """
        Generates a PDF document from a service order structure.
        
        Args:
            service_order: Dictionary containing the service order data
            output_path: Path where the PDF will be saved
            
        Returns:
            str: Path to the generated PDF file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = self._create_header(doc)
        
        # Process each ordem_servico in the response
        for ordem in service_order.get('ordem_servico', []):
            # Problem description
            elements.append(Paragraph('PROBLEMA', self.styles['SectionHeader']))
            elements.append(Paragraph(ordem['problema'], self.styles['Normal-Indent']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Steps
            elements.append(Paragraph('PROCEDIMENTOS', self.styles['SectionHeader']))
            for step in ordem['passos']:
                # Step header
                step_header = f"{step['ordem']}. {step['descricao']}"
                elements.append(Paragraph(step_header, self.styles['Normal-Bold']))
                
                # Justification
                elements.append(Paragraph(
                    f"Justificativa: {step['justificativa']}",
                    self.styles['Normal-Indent']
                ))
                
                # Duration
                elements.append(Paragraph(
                    f"Duração estimada: {step['duracao']}",
                    self.styles['Normal-Indent']
                ))
                
                # Safety measures
                if step['medidas_seguranca']:
                    elements.append(Paragraph(
                        "Medidas de Segurança:",
                        self.styles['Normal-Indent']
                    ))
                    elements.append(self._create_safety_measures_list(step['medidas_seguranca']))
                
                # Equipment for this step
                if step.get('equipamentos'):
                    elements.append(Paragraph(
                        "Equipamentos necessários:",
                        self.styles['Normal-Indent']
                    ))
                    elements.append(self._create_equipment_table(step['equipamentos']))
                
                elements.append(Spacer(1, 0.3*cm))
            
            # Total equipment needed
            if ordem.get('equipamentos_necessarios'):
                elements.append(Paragraph(
                    'LISTA COMPLETA DE EQUIPAMENTOS',
                    self.styles['SectionHeader']
                ))
                elements.append(self._create_equipment_table(ordem['equipamentos_necessarios']))
                elements.append(Spacer(1, 0.5*cm))
            
            # Observations
            if ordem.get('observacoes'):
                elements.append(Paragraph('OBSERVAÇÕES', self.styles['SectionHeader']))
                for obs in ordem['observacoes']:
                    elements.append(Paragraph(
                        f"• {obs}",
                        self.styles['Normal-Indent']
                    ))
                elements.append(Spacer(1, 0.5*cm))
            
            # References
            if ordem.get('referencias'):
                elements.append(Paragraph('REFERÊNCIAS', self.styles['SectionHeader']))
                for ref in ordem['referencias']:
                    elements.append(Paragraph(
                        f"• {ref}",
                        self.styles['Normal-Indent']
                    ))
            
            elements.append(Spacer(1, 1*cm))
        
        # Add signature fields
        elements.extend(self._create_signature_fields())
        
        # Generate the PDF
        doc.build(elements)
        return output_path
    
    def _create_signature_fields(self) -> List:
        """Creates signature fields at the bottom of the document."""
        elements = []
        
        # Create a table for signatures
        data = [
            ['_' * 40, '_' * 40],
            ['Responsável pela execução', 'Responsável pela aprovação'],
            ['Data: ___/___/___', 'Data: ___/___/___']
        ]
        
        signature_table = Table(data, colWidths=[8*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ]))
        
        elements.append(signature_table)
        return elements

# Example usage function
def generate_service_order_pdf(safety_response: Dict[str, Any], output_dir: str = "output") -> str:
    """
    Generate a PDF from a safety response.
    
    Args:
        safety_response: The response from the AI model
        output_dir: Directory where the PDF should be saved
        
    Returns:
        str: Path to the generated PDF file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"ordem_servico_{timestamp}.pdf")
    
    # Generate PDF
    generator = ServiceOrderPDFGenerator()
    pdf_path = generator.generate_pdf(safety_response, output_path)
    
    return pdf_path