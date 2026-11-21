"""Regresiones de memoria editorial. Las cuentas y métricas existen solo en temporales."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import datetime as dt
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import aprendizaje as cli
from herramientas import aprendizaje as a


class PruebasMemoria(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.cuenta="prueba"
        self.now=dt.datetime(2026,5,20,16,tzinfo=a.UTC)
        self.patch=patch.object(a,"ahora",return_value=self.now)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def evento(self,ident="serie",elegida="a"):
        return {"tipo":"decision","id":ident,"formato":"reel","elegida":elegida,
                "opciones":[{"id":"a","rasgos":["pregunta"]},{"id":"b","rasgos":["lista"]},
                            {"id":"c","formato":"carrusel","rasgos":["pregunta"]}]}

    def guardar(self,e):
        return a.registrar(self.root,self.cuenta,e)

    def leer(self):
        return a.resumen(self.root,self.cuenta)

    def muestra(self,dia,mid,value,formato="reel",edad=72,source="prueba temporal"):
        fecha=self.now-dt.timedelta(days=30-dia)
        met={"vistas":value,"me_gusta":value//5,"comentarios":value//25,"guardados":value//20,"alcance":1000}
        return {"tipo":"muestra","medio":str(mid),"formato":formato,"publicado":fecha.isoformat(),
                "observado":(fecha+dt.timedelta(hours=edad)).isoformat(),"metricas":met,"fuente":source}

    def test_seleccion_con_motivo_sin_inventarlo_y_ttl(self):
        eventos=[self.evento(str(i)) for i in range(3)]
        eventos[0]["motivo_admin"]="Se ve el taller."
        old=self.evento("antigua",elegida="b")
        old["fecha"]=(self.now-dt.timedelta(days=91)).isoformat()
        a.registrar_lote(self.root,self.cuenta,eventos+[old])
        r=self.leer()
        self.assertEqual(len(r["decisiones"]),4)
        self.assertEqual(sum("motivo_admin" in x for x in r["decisiones"]),1)
        fav=next(x for x in r["preferencias_inferidas"] if x["rasgo"]=="pregunta")
        self.assertEqual((fav["elecciones"],fav["comparaciones"],fav["fraccion_ofrecida"]),(3,3,.5))
        anti=next(x for x in r["preferencias_inferidas"] if x["rasgo"]=="lista")
        self.assertEqual(anti["direccion"],"menos_elegido")
        self.assertFalse(r["hipotesis_rendimiento"])
        self.assertFalse(r["publicaciones"])
        self.assertFalse(a.resumen(self.root,"otra")["decisiones"])

    def test_una_eleccion_sin_motivo_conserva_alternativas_y_prueba_en_markdown(self):
        e=self.evento("primera")
        e["opciones"][0].update(titulo="Taller en primer plano",rasgos=["pregunta","taller"])
        e["opciones"][1].update(titulo="Lista del taller",rasgos=["lista","taller"])
        self.guardar(e)
        r=self.leer()
        self.assertFalse(r["preferencias_inferidas"])
        contraste=r["contrastes_decisiones"][0]
        self.assertEqual(contraste["alternativas"][0]["solo_elegida"],["pregunta"])
        self.assertEqual(contraste["alternativas"][0]["comunes"],["taller"])
        self.assertEqual(contraste["alternativas"][0]["solo_alternativa"],["lista"])
        md=(self.root/"memoria/prueba/MEMORIA.md").read_text(encoding="utf8")
        for phrase in ("Motivo sin declarar","Lista del taller","solo etiquetado en la elegida «pregunta»",
                       "etiquetado en ambas «taller»","el formato cambia de reel a carrusel",
                       "variar únicamente «pregunta»","instrucciones vigentes"):
            self.assertIn(phrase,md)

    def test_historial_conflicto_retiro_y_aislamiento(self):
        a1={"tipo":"instruccion","id":"tono","directriz":"Usar tuteo.","fuente":"chat demo"}
        self.assertEqual(self.guardar(a1)["revision"],1)
        self.assertFalse(self.guardar(a1)["cambio"])
        self.guardar(dict(a1,directriz="Tutear en el reel.",si_revision=1))
        with self.assertRaisesRegex(ValueError,"Conflicto"):
            self.guardar(dict(a1,directriz="otra",si_revision=1))
        self.guardar({"tipo":"retirar","clase":"instruccion","id":"tono","motivo":"Sustituida.","si_revision":2})
        self.assertEqual(len(a.historial(self.root,self.cuenta,"instruccion","tono")),3)
        self.assertFalse(self.leer()["instrucciones"])
        with self.assertRaises(ValueError):
            self.guardar(dict(a1,cuenta="ajena"))
        ruta=self.root/"memoria/prueba/MEMORIA.md"
        self.assertTrue(ruta.exists())
        ruta.write_text("proyección interrumpida",encoding="utf8")
        self.leer()
        self.assertNotIn("interrumpida",ruta.read_text(encoding="utf8"))

    def test_concurrencia_y_rollback(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            recibos=list(pool.map(lambda _:self.guardar(self.evento()),range(10)))
        self.assertEqual(sum(x["cambio"] for x in recibos),1)
        with self.assertRaises(ValueError):
            a.registrar_lote(self.root,self.cuenta,[self.evento("nuevo"),dict(self.evento(),elegida="ausente")])
        self.assertEqual([x["id"] for x in self.leer()["decisiones"]],["serie"])

    def test_comparacion_rendimiento_y_post_sin_etiquetar(self):
        events=[self.muestra(i,100+i,n) for i,n in enumerate([100,90,120,110,100,240,250,260])]
        events+=[self.muestra(i,200+i,9000,"carrusel") for i in range(4)]
        events+=[self.muestra(0,100,2000,edad=160),self.muestra(7,107,700,edad=74)]
        for mid in (105,106,107):
            events.append({"tipo":"etiquetas","id":str(mid),"rasgos":["línea de luz"],"formato":"reel","fuente":"lectura documentada"})
        a.registrar_lote(self.root,self.cuenta,events)
        r=self.leer()
        winner=next(m for m in r["comparaciones"] if m["medio"]=="105")
        self.assertEqual(winner["senales"]["vistas"]["n"],5)
        self.assertEqual(winner["senales"]["me_gusta"]["unidad"],"por_1000_alcanzadas")
        self.assertGreater(winner["indice"],2)
        self.assertEqual(r["hipotesis_rendimiento"][0]["medios"],["105","106","107"])
        self.assertIn("100",r["medios_sin_etiquetar"])
        self.assertFalse(r["preferencias_inferidas"])

    def test_ausentes_ventana_base_minima_e_instruccion(self):
        events=[]
        for i in range(8):
            e=self.muestra(i,300+i,100)
            e["metricas"]={"vistas":300,"comentarios":0,"guardados":None}
            events.append(e)
        events.append(self.muestra(10,405,600,edad=400))
        a.registrar_lote(self.root,self.cuenta,events)
        resumen=self.leer()
        self.assertEqual(len(resumen["publicaciones"]),9)
        self.assertTrue(all(r["indice"] is None for r in resumen["comparaciones"]))
        latest=next(x for x in resumen["publicaciones"] if x["medio"]=="305")
        self.assertEqual(latest["metricas"],{"vistas":300,"comentarios":0})
        self.assertFalse(any(x["medio"]=="405" for x in resumen["comparaciones"]))

    def test_api_solo_lectura_identidad_parciales_y_vinculo_por_huella(self):
        root=self.root
        (root/"operacion.toml").write_text('cuenta="prueba"\n',encoding="utf8")
        e=self.evento()
        e["opciones"][0]["huella_publicacion"]="digest:caption"
        self.guardar(e)
        estado=root/"estado"
        estado.mkdir()
        with closing(sqlite3.connect(estado/"acciones.sqlite")) as db, db:
            db.execute("CREATE TABLE acciones(clave TEXT,huella TEXT,remoto TEXT,estado TEXT)")
            db.execute("INSERT INTO acciones VALUES('77:feed:2026-05-17','digest:caption','123','confirmado')")
        class Meta:
            account="77"
            def identity(self,config):
                return {"id":"77","username":"prueba"}
            def pages(self,path,fields):
                return [{"id":"123","timestamp":"2026-05-17T16:00:00+00:00","username":"prueba","media_product_type":"REELS","comments_count":0},
                        {"id":"888","timestamp":"2026-05-17T17:00:00+00:00","username":"ajena","media_product_type":"REELS"}]
            def api(self,path,params):
                if "," in params["metric"]:
                    raise RuntimeError("Falta una métrica")
                if params["metric"]=="views":
                    return {"data":[{"name":"views","values":[{"value":55}]}]}
                if params["metric"]=="reach":
                    return {"data":[{"name":"reach","total_value":{"value":40}}]}
                if params["metric"]=="shares":
                    return {"data":[{"name":"shares","values":[{"value":3}]}]}
                raise RuntimeError("No disponible")
        with patch.object(cli,"ahora",return_value=self.now):
            resultado=cli.sincronizar(root,self.cuenta,Meta())
            repetido=cli.sincronizar(root,self.cuenta,Meta())
            self.assertEqual(resultado["vinculos_confirmados"],1)
            self.assertEqual(repetido["cambios"],0)
        r=self.leer()
        self.assertEqual(r["publicaciones"][0]["metricas"],{"comentarios":0,"vistas":55,"alcance":40,"compartidos":3})
        self.assertNotIn("compartidos",a.PESOS)
        self.assertEqual(r["comparaciones"][0]["rasgos"],["pregunta"])
        with self.assertRaisesRegex(ValueError,"no coincide"):
            cli.sincronizar(root,"otra",Meta())

    def test_paginacion_se_detiene_con_suficientes_o_con_500_filas(self):
        (self.root/"operacion.toml").write_text('cuenta="prueba"\n',encoding="utf8")
        class Coleccion:
            account="77"
            iter_rows=cli.Meta.iter_rows
            def __init__(self,kind):
                self.kind=kind
                self.requested=[]
            def identity(self,config):
                return {"id":self.account,"username":config["cuenta"]}
            def api(self,path,params):
                self.requested.append(params["limit"])
                start=int(params.get("after","0"))
                end=start+params["limit"]
                return {"data":[{"id":str(i),"timestamp":"2026-05-01T00:00:00Z",
                                 "media_product_type":self.kind} for i in range(start,end)],
                        "paging":{"next":"siguiente","cursors":{"after":str(end)}}}
        corta=Coleccion("REELS")
        r=cli.sincronizar(self.root,self.cuenta,corta,limite=3,solo_publicas=True)
        self.assertEqual((r["capturas"],r["medios_revisados"],corta.requested),(3,3,[3]))
        larga=Coleccion("FEED")
        r=cli.sincronizar(self.root,self.cuenta,larga,limite=48,solo_publicas=True)
        self.assertEqual((r["capturas"],r["medios_revisados"],sum(larga.requested)),(0,500,500))
        self.assertEqual(larga.requested[-1],20)

    def test_cli_en_archivo_y_radar_idempotente(self):
        ins={"tipo":"instruccion","id":"real","directriz":"Una CTA.","fuente":"prueba aislada"}
        path=self.root/"entrada.json"
        path.write_text(json.dumps(ins),encoding="utf8")
        cmd=[sys.executable,"-B",str(Path(cli.__file__)),"--raiz",str(self.root),"--cuenta",self.cuenta]
        p=subprocess.run(cmd+["registrar",str(path)],capture_output=True,check=True)
        self.assertTrue(json.loads(p.stdout)["cambio"])
        out=subprocess.run(cmd+["historial","instruccion","real"],capture_output=True,check=True)
        self.assertEqual(json.loads(out.stdout)[0]["revision"],1)
        state=self.root/"estado"
        state.mkdir()
        with closing(sqlite3.connect(state/"radar.sqlite")) as db, db:
            db.execute("CREATE TABLE muestras(cuenta,medio,publicado,observado,vistas,enlace)")
            db.execute("INSERT INTO muestras VALUES('prueba','999','2026-05-17T16:00:00Z','2026-05-20T16:00:00Z',40,'')")
        self.assertEqual(cli.importar_radar(self.root,self.cuenta)["incorporadas"],1)
        self.assertEqual(cli.importar_radar(self.root,self.cuenta)["incorporadas"],0)
        self.assertEqual(self.leer()["publicaciones"][0]["metricas"],{"vistas":40})


if __name__=="__main__":
    unittest.main()
