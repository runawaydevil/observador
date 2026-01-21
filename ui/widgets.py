from textual.widgets import Static
from rich.text import Text
from rich.table import Table
from rich.console import RenderableType


class FooterWidget(Static):
    def render(self) -> RenderableType:
        return Text("Desenvolvido pela 0xpblab — https://0xpblab.org", style="dim white")


class ReadingDisplay(Static):
    def __init__(self, reading_data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reading_data = reading_data
    
    def render(self) -> RenderableType:
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text
        
        correspondencias = self.reading_data.get("correspondencias", {})
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Posição", style="cyan")
        table.add_column("Símbolo", style="yellow")
        table.add_column("Elemento", style="green")
        table.add_column("Qualidade", style="blue")
        
        for pos, key in [("Passado", "passado"), ("Presente", "presente"), ("Tendência", "tendencia")]:
            if key in correspondencias:
                sym = correspondencias[key]
                table.add_row(
                    pos,
                    f"{sym.get('glifo', '')} {sym.get('nome', '')}",
                    sym.get('elemento', ''),
                    sym.get('qualidade', '')
                )
        
        seal = Text(self.reading_data.get("seal", ""), style="bold yellow")
        liturgy = Text(self.reading_data.get("liturgy", ""), style="cyan")
        reading = Text(self.reading_data.get("reading", ""), style="white")
        coda = Text(self.reading_data.get("coda", ""), style="bold magenta")
        
        ato = Text(f"ATO: {self.reading_data.get('ato', '')}", style="bold green")
        preco = Text(f"PREÇO: {self.reading_data.get('preco', '')}", style="bold red")
        
        return Group(
            Panel(table, title="Correspondências", border_style="blue"),
            Panel(seal, border_style="yellow"),
            Panel(liturgy, border_style="cyan"),
            Panel(reading, border_style="white"),
            Panel(coda, border_style="magenta"),
            Panel(Group(ato, preco), title="Resumo", border_style="green")
        )


class CorrespondenceTable(Static):
    def __init__(self, correspondencias: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correspondencias = correspondencias
    
    def render(self) -> RenderableType:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Posição")
        table.add_column("Símbolo")
        table.add_column("Elemento")
        table.add_column("Planeta")
        table.add_column("Qualidade")
        
        for pos, key in [("Passado", "passado"), ("Presente", "presente"), ("Tendência", "tendencia")]:
            if key in self.correspondencias:
                sym = self.correspondencias[key]
                table.add_row(
                    pos,
                    f"{sym.get('glifo', '')} {sym.get('nome', '')}",
                    sym.get('elemento', ''),
                    sym.get('planeta', ''),
                    sym.get('qualidade', '')
                )
        
        return table
